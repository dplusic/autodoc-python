from .cli.commands.index.index import index
from .data_types import AutodocRepoConfig


def main() -> None:
    index(AutodocRepoConfig(
        name="autodoc-python",
        repository_url="https://github.com/dplusic/autodoc-python",
        root=".",
        output="./.autodoc",
        llms=[
        ],
        ignore=[
            ".*",
            "*package-lock.json",
            "*package.json",
            "node_modules",
            "*dist*",
            "*build*",
            "*test*",
            "*.svg",
            "*.md",
            "*.mdx",
            "*.toml",
            "*autodoc*",
        ],
        file_prompt="Write a detailed technical explanation of what this code does. \n      Focus on the high-level purpose of the code and how it may be used in the larger project.\n      Include code examples where appropriate. Keep you response between 100 and 300 words. \n      DO NOT RETURN MORE THAN 300 WORDS.\n      Output should be in markdown format.\n      Do not just list the methods and classes in this file.",
        folder_prompt="Write a technical explanation of what the code in this file does\n      and how it might fit into the larger project or work with other parts of the project.\n      Give examples of how this code might be used. Include code examples where appropriate.\n      Be concise. Include any information that may be relevant to a developer who is curious about this code.\n      Keep you response under 400 words. Output should be in markdown format.\n      Do not just list the files and folders in this folder.",
        chat_prompt="",
        content_type="code",
        target_audience="smart developer",
        link_hosted=True,
    ))


if __name__ == '__main__':
    main()
