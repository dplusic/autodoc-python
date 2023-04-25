import os
from typing import List

from langchain.document_loaders.base import BaseLoader
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter

from ....data_types import AutodocRepoConfig


def readdir(directory_path: str) -> List[str]:
    files = []
    for dirpath, dirnames, filenames in os.walk(directory_path):
        for filename in filenames:
            files.append(os.path.join(dirpath, filename))
    return files


def process_file(file_path: str) -> Document:
    with open(file_path, 'r') as file:
        file_contents = file.read()
    metadata = {"source": file_path}
    doc = Document(
        page_content=file_contents,
        metadata=metadata,
    )
    return doc


def process_directory(directory_path: str) -> List[Document]:
    docs = []
    try:
        files = readdir(directory_path)
    except FileNotFoundError as e:
        raise Exception(f"Could not read directory: {directory_path}. Did you run `sh download.sh`?") from e
    for file in files:
        file_path = os.path.join(directory_path, file)
        if os.path.isdir(file_path):
            nested_docs = process_directory(file_path)
            docs += nested_docs
        else:
            doc = process_file(file_path)
            docs.append(doc)
    return docs


class RepoLoader(BaseLoader):
    def __init__(self, file_path: str):
        self.file_path = file_path

    def load(self) -> List[Document]:
        return process_directory(self.file_path)


def create_vector_store(config: AutodocRepoConfig) -> None:
    root = config.root
    output = config.output

    loader = RepoLoader(root)
    raw_docs = loader.load()

    # Split the text into chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=8000,
        chunk_overlap=100,
    )
    docs = text_splitter.split_documents(raw_docs)
    # TODO
    # Create the vectorstore
    # vector_store = HNSWLib.from_documents(docs, OpenAIEmbeddings())
    # vector_store.save(output)
