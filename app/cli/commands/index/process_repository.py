import hashlib
import json
import os
import re
import sys
from typing import List
from typing import Optional

from langchain.llms import OpenAIChat
from tiktoken import encoding_for_model

from .prompts import create_code_file_summary, create_code_questions, folder_summary_prompt
from ...utils.api_rate_limit import APIRateLimit
from ...utils.file_util import github_file_url, get_file_name, github_folder_url
from ...utils.traverse_file_system import traverse_file_system
from ....data_types import AutodocRepoConfig, LLMModelDetails, FileSummary, FolderSummary, TraverseFileSystemParams, \
    ProcessFolderParams, ProcessFileParams


def process_repository(
        config: AutodocRepoConfig,
        dry_run: Optional[bool] = None,
):
    project_name = config.name
    repository_url = config.repository_url
    input_root = config.root
    output_root = config.output
    ignore = config.ignore
    file_prompt = config.file_prompt
    folder_prompt = config.folder_prompt
    content_type = config.content_type
    target_audience = config.target_audience
    link_hosted = config.link_hosted

    encoding = encoding_for_model("gpt-3.5-turbo")
    rate_limit = APIRateLimit(25)

    def call_llm(
            prompt: str,
            model: OpenAIChat,
    ) -> str:
        return rate_limit.call_api(lambda: model(prompt))

    def is_model(model: Optional[LLMModelDetails]) -> bool:
        return model is not None

    def process_file(params: ProcessFileParams) -> None:
        file_name = params.file_name
        file_path = params.file_path
        project_name = params.project_name
        content_type = params.content_type
        file_prompt = params.file_prompt
        target_audience = params.target_audience
        link_hosted = params.link_hosted

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        """
        Calculate the checksum of the file content
        """
        new_checksum = calculate_checksum([content])

        """
        If an existing .json file exists,
        it will check the checksums and decide if a reindex is needed
        """
        reindex = should_reindex(
            os.path.join(output_root, file_path[0:file_path.rfind("\\")]),
            re.sub(r"\.[^/.]+$", ".json", file_name),
            new_checksum,
        )
        if not reindex:
            return

        markdown_file_path = os.path.join(output_root, file_path)
        url = github_file_url(repository_url, input_root, file_path, link_hosted)
        summary_prompt = create_code_file_summary(
            project_name,
            project_name,
            content,
            content_type,
            file_prompt,
        )
        questions_prompt = create_code_questions(
            project_name,
            project_name,
            content,
            content_type,
            target_audience,
        )
        summary_length = len(encoding.encode(summary_prompt))
        question_length = len(encoding.encode(questions_prompt))
        # max_length = max(question_length, summary_length)

        """
        TODO: Encapsulate logic for selecting the best model
        TODO: Allow for different selection strategies based
        TODO: preference for cost/performance
        TODO: When this is re-written, it should use the correct
        TODO: TikToken encoding for each model
        """

        model: Optional[LLMModelDetails] = None  # TODO

        if not is_model(model):
            # print(f"Skipped {file_path} | Length ${max_length}")
            return

        try:
            if not dry_run:
                """ Call LLM """
                # TODO parallel
                summary, questions = (
                    call_llm(summary_prompt, model.llm),
                    call_llm(questions_prompt, model.llm)
                )

                """
                Create file and save to disk
                """
                file = FileSummary(
                    file_name=file_name,
                    file_path=file_path,
                    url=url,
                    summary=summary,
                    questions=questions,
                    checksum=new_checksum,
                )

                output_path = get_file_name(markdown_file_path, ".", ".json")
                content = json.dumps(file, indent=2) if len(file.summary) > 0 else ""

                """
                Create the output directory if it doesn't exist
                """
                try:
                    os.makedirs(markdown_file_path.replace(file_name, ""), exist_ok=True)
                    with open(output_path, "w", encoding="utf-8") as f:
                        f.write(content)
                except Exception as e:
                    print(repr(e), file=sys.stderr)
                    return

                # print(f"File: {file_name} => {output_path}")

            """
            Track usage for end of run summary
            """
            model.input_tokens += summary_length + question_length
            model.total += 1
            model.output_tokens += 1000
            model.succeeded += 1
        except Exception as e:
            print(repr(e))
            print(f"Failed to get summary for file {file_name}", file=sys.stderr)
            model.failed += 1

    def process_folder(params: ProcessFolderParams) -> None:
        folder_name = params.folder_name
        folder_path = params.folder_path
        project_name = params.project_name
        content_type = params.content_type
        folder_prompt = params.folder_prompt
        should_ignore = params.should_ignore
        link_hosted = params.link_hosted

        """
        For now we don't care about folders

        TODO: Add support for folders during estimation
        """
        if dry_run:
            return

        contents = [file_name for file_name in os.listdir(folder_path) if not should_ignore(file_name)]

        """
        Get the checksum of the folder
        """
        new_checksum = calculate_checksum(contents)

        """
        If an existing summary.json file exists,
        it will check the checksums and decide if a reindex is needed
        """
        reindex = should_reindex(
            folder_path,
            "summary.json",
            new_checksum,
        )
        if not reindex:
            return

        url = github_folder_url(repository_url, input_root, folder_path, link_hosted)
        all_files = []
        for file_name in contents:
            entry_path = os.path.join(folder_path, file_name)

            if os.path.isfile(entry_path) and file_name != "summary.json":
                with open(entry_path, "r", encoding="utf-8") as f:
                    file = f.read()
                all_files.append(json.loads(file) if len(file) > 0 else None)
            else:
                all_files.append(None)

        try:
            files = [file for file in all_files if file is not None]
            all_folders = []
            for file_name in contents:
                entry_path = os.path.join(folder_path, file_name)

                if os.path.isdir(entry_path):
                    try:
                        summary_file_path = os.path.join(entry_path, "summary.json")
                        with open(summary_file_path, "r", encoding="utf-8") as f:
                            file = f.read()
                        all_folders.append(json.loads(file))
                    except:
                        print(f"Skipped: {folder_path}")
                        all_folders.append(None)
                else:
                    all_folders.append(None)

            folders = [folder for folder in all_folders if folder is not None]

            summary = call_llm(
                folder_summary_prompt(
                    folder_path,
                    project_name,
                    files,
                    folders,
                    content_type,
                    folder_prompt,
                ),
                OpenAIChat(),  # TODO
            )

            folder_summary = FolderSummary(
                folder_name=folder_name,
                folder_path=folder_path,
                url=url,
                files=files,
                folders=[folder for folder in folders if folder],
                summary=summary,
                questions="",
                checksum=new_checksum,
            )

            output_path = os.path.join(folder_path, "summary.json")
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(json.dumps(folder_summary, indent=2))

            # print(f"Folder: {folder_name} => {output_path}")
        except Exception as e:
            print(repr(e))
            print(f"Failed to get summary for folder: {folder_path}")

    # def files_and_folders() -> Dict[str, int]:
    #     """
    #     Get the number of files and folders in the project
    #     """
    #     files = 0
    #     folders = 0
    #
    #     def inc_files():
    #         nonlocal files
    #         files += 1
    #
    #     def inc_folders():
    #         nonlocal folders
    #         folders += 1
    #
    #     traverse_file_system(TraverseFileSystemParams(
    #         input_path=input_root,
    #         project_name=project_name,
    #         process_file=inc_files,
    #         process_folder=None,
    #         ignore=ignore,
    #         file_prompt=file_prompt,
    #         folder_prompt=folder_prompt,
    #         content_type=content_type,
    #         target_audience=target_audience,
    #         link_hosted=link_hosted,
    #     ))
    #     traverse_file_system(TraverseFileSystemParams(
    #         input_path=input_root,
    #         project_name=project_name,
    #         process_file=None,
    #         process_folder=inc_folders,
    #         ignore=ignore,
    #         file_prompt=file_prompt,
    #         folder_prompt=folder_prompt,
    #         content_type=content_type,
    #         target_audience=target_audience,
    #         link_hosted=link_hosted,
    #     ))
    #
    #     return {
    #         "files": files,
    #         "folders": folders,
    #     }

    # files, folders = files_and_folders().values()

    """
    Create markdown files for each code file in the project
    """

    # update_spinner_text(f"Processing {files} files...")
    traverse_file_system(TraverseFileSystemParams(
        input_path=input_root,
        project_name=project_name,
        process_file=process_file,
        process_folder=None,
        ignore=ignore,
        file_prompt=file_prompt,
        folder_prompt=folder_prompt,
        content_type=content_type,
        target_audience=target_audience,
        link_hosted=link_hosted,
    ))
    # spinner_success(f"Processing {files} files...")

    """
    Create markdown summaries for each folder in the project
    """
    # update_spinner_text(f"Processing {folders} folders... ")
    traverse_file_system(TraverseFileSystemParams(
        input_path=output_root,
        project_name=project_name,
        process_file=None,
        process_folder=process_folder,
        ignore=ignore,
        file_prompt=file_prompt,
        folder_prompt=folder_prompt,
        content_type=content_type,
        target_audience=target_audience,
        link_hosted=link_hosted,
    ))
    # spinner_success(f"Processing {folders} folders... ")
    # stop_spinner()


def calculate_checksum(contents: List[str]) -> str:
    """
    Calculates the checksum of all the files in a folder
    """
    checksums = []
    for content in contents:
        checksum = hashlib.md5(content.encode("utf-8")).hexdigest()
        checksums.append(checksum)
    concatenated_checksum = "".join(checksums)
    final_checksum = hashlib.md5(concatenated_checksum.encode("utf-8")).hexdigest()
    return final_checksum


def should_reindex(
        content_path: str,
        name: str,
        new_checksum: str,
) -> bool:
    """
    Checks if a summary.json file exists.
    If it does, compares the checksums to see if it
    needs to be re-indexed or not.
    """
    json_path = os.path.join(content_path, name)

    summary_exists = os.access(json_path, os.F_OK)

    if summary_exists:
        with open(json_path, "r", encoding="utf-8") as f:
            file_contents = f.read()
        file_contents_json = json.loads(file_contents)

        old_checksum = file_contents_json["checksum"]

        if old_checksum == new_checksum:
            print(f"Skipping {json_path} because it has not changed")
            return False
        else:
            print(f"Reindexing {json_path} because it has changed")
            return True

    # if no summary then generate one
    return True
