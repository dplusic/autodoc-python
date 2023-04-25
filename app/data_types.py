from dataclasses import dataclass
from typing import List, TypeAlias, Callable, Optional

from langchain.llms import OpenAIChat


@dataclass
class AutodocRepoConfig:
    name: str
    repository_url: str
    root: str
    output: str
    llms: List[str]
    ignore: List[str]
    file_prompt: str
    folder_prompt: str
    chat_prompt: str
    content_type: str
    target_audience: str
    link_hosted: bool


@dataclass
class FileSummary:
    file_name: str
    file_path: str
    url: str
    summary: str
    questions: str
    checksum: str


@dataclass
class ProcessFileParams:
    file_name: str
    file_path: str
    project_name: str
    content_type: str
    file_prompt: str
    target_audience: str
    link_hosted: bool


ProcessFile: TypeAlias = Callable[[ProcessFileParams], None]


@dataclass
class FolderSummary:
    folder_name: str
    folder_path: str
    url: str
    files: List[FileSummary]
    folders: "List[FolderSummary]"
    summary: str
    questions: str
    checksum: str


@dataclass
class ProcessFolderParams:
    input_path: str
    folder_name: str
    folder_path: str
    project_name: str
    content_type: str
    folder_prompt: str
    target_audience: str
    link_hosted: bool
    should_ignore: Callable[[str], bool]


ProcessFolder: TypeAlias = Callable[[ProcessFolderParams], None]


@dataclass
class TraverseFileSystemParams:
    input_path: str
    project_name: str
    process_file: Optional[ProcessFile]
    process_folder: Optional[ProcessFolder]
    ignore: List[str]
    file_prompt: str
    folder_prompt: str
    content_type: str
    target_audience: str
    link_hosted: bool


@dataclass
class LLMModelDetails:
    name: str
    input_cost_per_1k_tokens: float
    output_cost_per_1k_tokens: float
    max_length: int
    llm: OpenAIChat
    input_tokens: int
    output_tokens: int
    succeeded: int
    failed: int
    total: int
