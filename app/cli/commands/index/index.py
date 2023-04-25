import dataclasses
import os.path

from .create_vector_store import create_vector_store
from .process_repository import process_repository
from ....data_types import AutodocRepoConfig


def index(config: AutodocRepoConfig) -> None:
    output = config.output

    json = os.path.join(output, 'docs', 'json')
    markdown = os.path.join(output, 'docs', 'markdown')
    data = os.path.join(output, 'docs', 'data')

    """
    Traverse the repository, call LLMs for each file,
    and create JSON files with the results.
    """

    # updateSpinnerText('Processing repository...')
    process_repository(dataclasses.replace(
        config,
        output=json,
    ))
    # updateSpinnerText('Processing repository...')
    # spinnerSuccess()

    """
    Create markdown files from JSON files
    """
    # updateSpinnerText('Creating markdown files...')
    # convert_json_to_markdown({
    #     "name": name,
    #     "repositoryUrl": repositoryUrl,
    #     "root": json_dir,
    #     "output": markdown_dir,
    #     "llms": llms,
    #     "ignore": ignore,
    #     "filePrompt": filePrompt,
    #     "folderPrompt": folderPrompt,
    #     "chatPrompt": chatPrompt,
    #     "contentType": contentType,
    #     "targetAudience": targetAudience,
    #     "linkHosted": linkHosted
    # })
    # spinnerSuccess()

    # updateSpinnerText('Create vector files...')
    create_vector_store(dataclasses.replace(
        config,
        root=markdown,
        output=data,
    ))
    # spinnerSuccess()
