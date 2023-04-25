import os
import sys
from fnmatch import fnmatch
from typing import AnyStr

from ...data_types import TraverseFileSystemParams, ProcessFolderParams, ProcessFileParams


def traverse_file_system(
        params: TraverseFileSystemParams,
) -> None:
    try:
        input_path = params.input_path
        project_name = params.project_name
        process_file = params.process_file
        process_folder = params.process_folder
        ignore = params.ignore
        file_prompt = params.file_prompt
        folder_prompt = params.folder_prompt
        content_type = params.content_type
        target_audience = params.target_audience
        link_hosted = params.link_hosted

        if not os.access(input_path, mode=os.F_OK):
            print("The provided folder path does not exist.")
            return

        def should_ignore(file_name: str) -> bool:
            return any(fnmatch(file_name, pattern) for pattern in ignore)

        def dfs(current_path: str) -> None:
            contents = [
                file_name
                for file_name in os.listdir(current_path)
                if not should_ignore(file_name)
            ]

            for folder_name in contents:
                folder_path = os.path.join(current_path, folder_name)

                if os.path.isdir(folder_path):
                    dfs(folder_path)

                    if process_folder:
                        process_folder(ProcessFolderParams(
                            input_path=input_path,
                            folder_name=folder_name,
                            folder_path=folder_path,
                            project_name=project_name,
                            should_ignore=should_ignore,
                            folder_prompt=folder_prompt,
                            content_type=content_type,
                            target_audience=target_audience,
                            link_hosted=link_hosted,
                        ))

            for file_name in contents:
                file_path = os.path.join(current_path, file_name)

                if not os.path.isfile(file_path):
                    continue

                with open(file_path, "rb") as f:
                    buffer = f.read()

                if is_text(buffer):
                    if process_file:
                        process_file(ProcessFileParams(
                            file_name=file_name,
                            file_path=file_path,
                            project_name=project_name,
                            file_prompt=file_prompt,
                            content_type=content_type,
                            target_audience=target_audience,
                            link_hosted=link_hosted,
                        ))

        dfs(input_path)
    except Exception as e:
        print(f"Error during traversal: {e}", file=sys.stderr)
        raise e


def is_text(buffer: AnyStr):
    try:
        buffer.decode("utf-8")
        return True
    except UnicodeDecodeError:
        return False
