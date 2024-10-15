import os
import re
import sys
from typing import List, Tuple, Optional

from colorama import Fore, Style, init

from ..Tools.MaybeMonad import Maybe
from ..Tools import logger

init(autoreset=True)

HEADER_MD = """\
# Combined Files Reference

This is a combined file representative of a folder structure, only used as reference.
"""

USAGE_TEXT = f"""
{Fore.GREEN}{Style.BRIGHT}--- Combine Files Documentation---{Style.RESET_ALL}

This script combines files from the current working directory into a single markdown file.
It's useful for sharing data with other developers or feeding it to Large Language Models (LLMs) for analysis or questions.

{Fore.YELLOW}{Style.BRIGHT}Usage:{Style.RESET_ALL}
  combine-files [output_file]

{Fore.YELLOW}{Style.BRIGHT}Arguments:{Style.RESET_ALL}
  {Fore.YELLOW}--> Output file:{Style.RESET_ALL} Path to output file (default is 'combined_file.md')

{Fore.CYAN}{Style.BRIGHT}Commands:{Style.RESET_ALL}
  -->{Fore.CYAN}{Style.BRIGHT} -h{Style.RESET_ALL} or {Fore.CYAN}{Style.BRIGHT}--help{Style.RESET_ALL}: Prints this help message
  -->{Fore.CYAN}{Style.BRIGHT} -y{Style.RESET_ALL} or {Fore.CYAN}{Style.BRIGHT}--skip-input{Style.RESET_ALL}: Skips user input confirmation
  -->{Fore.CYAN}{Style.BRIGHT} --test-mode{Style.RESET_ALL}: Test run, only lists number of files and paths it will combine
  -->{Fore.CYAN}{Style.BRIGHT} --debug-mode{Style.RESET_ALL}: Prints debug information step by step
  -->{Fore.CYAN}{Style.BRIGHT} --all-files{Style.RESET_ALL}: Includes all files in the directory
  -->{Fore.CYAN}{Style.BRIGHT} --include-file-name{Style.RESET_ALL}: Includes file's content matching the specified pattern
  -->{Fore.CYAN}{Style.BRIGHT} --exclude-file-name{Style.RESET_ALL}: Excludes file's content matching the specified pattern
  -->{Fore.CYAN}{Style.BRIGHT} --include-ext{Style.RESET_ALL}: Includes files with specified extensions
  -->{Fore.CYAN}{Style.BRIGHT} --compact-mode{Style.RESET_ALL}: Reduces tokenization by removing docstrings and copyright
  -->{Fore.CYAN}{Style.BRIGHT} --no-tree{Style.RESET_ALL}: Disables listing the directory structure
  -->{Fore.CYAN}{Style.BRIGHT} --filter-tree{Style.RESET_ALL}: Filters the directory tree to only include files

{Fore.GREEN}{Style.BRIGHT}Examples:{Style.RESET_ALL}
{Fore.LIGHTBLACK_EX}1: Compact mode {Style.RESET_ALL}
  combine-files {Fore.CYAN}--compact-mode
{Fore.LIGHTBLACK_EX}2: Includes py, json, md files and runs in compact mode {Style.RESET_ALL}
  combine-files {Fore.YELLOW}output.md {Fore.CYAN}--include-ext [.py, .json, .md] --compact-mode
{Fore.LIGHTBLACK_EX}3: Includes files with specified names and extensions {Style.RESET_ALL}
  combine-files {Fore.CYAN}--include-file-name [__init__, test.json] --include-ext [.py, .json]
{Fore.LIGHTBLACK_EX}4: Debug, test mode, no input, includes the content of __init__.py or test.json {Style.RESET_ALL}
  combine-files {Fore.CYAN}--debug-mode --test-mode --skip-input --include-file-name [__init__, test.json] --include-ext [.py, .json]
{Fore.LIGHTBLACK_EX}5: Includes all files in the directory {Style.RESET_ALL}
  combine-files {Fore.CYAN}--all-files
{Fore.LIGHTBLACK_EX}6: Disables listing the directory structure {Style.RESET_ALL}
  combine-files {Fore.CYAN}--no-tree
{Fore.LIGHTBLACK_EX}7: Filters the directory tree to only include files {Style.RESET_ALL}
  combine-files {Fore.CYAN}--filter-tree

{Fore.GREEN}----------------------------{Style.RESET_ALL}
"""

class FileCombiner:
    def __init__(self, directory: str, output_file: str = 'combined_file.md', extensions: Optional[List[str]] = None,
                 compact_mode: bool = False, include_patterns: Optional[List[str]] = None,
                 exclude_patterns: Optional[List[str]] = None, debug: bool = False, tree: bool = True,
                 filter_tree: bool = False):
        """
        Initialize the FileCombiner instance.

        :param directory: Directory to scan for files.
        :param output_file: Name of the output file.
        :param extensions: List of file extensions to include.
        :param compact_mode: Flag to enable compact mode.
        :param include_patterns: List of patterns to include.
        :param exclude_patterns: List of patterns to exclude.
        :param debug: Flag to enable debug mode.
        :param tree: Flag to include directory structure.
        :param filter_tree: Flag to filter the directory tree.
        """
        self.directory = directory
        self.output_file = output_file
        self.extensions = extensions if extensions else ['.py']
        self.compact_mode = compact_mode
        self.include_patterns = include_patterns if include_patterns else []
        self.exclude_patterns = exclude_patterns if exclude_patterns else []
        self.debug = debug
        self.tree = tree
        self.filter_tree = filter_tree

    def get_files_by_extension(self) -> Tuple[List[Tuple[str, str]], List[str]]:
        """
        Recursively get all files with specified extensions in the directory.

        :return: A tuple containing a list of files and the directory structure.
        """
        logger.debug(f"Scanning directory: {self.directory} for extensions: {self.extensions}")
        files = []
        directory_structure = []
        for root, _, files_in_dir in os.walk(self.directory):
            for file in files_in_dir:
                if self.extensions == '*' or any(file.endswith(ext) for ext in self.extensions):
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, self.directory)
                    if os.path.abspath(file_path) == os.path.abspath(self.output_file):
                        logger.debug(f"Avoiding file: {file_path}")
                        continue
                    directory_structure.append(relative_path)
                    if self.include_patterns and not any(inc in file for inc in self.include_patterns):
                        continue
                    if self.exclude_patterns and any(exc in file for exc in self.exclude_patterns):
                        continue
                    files.append((relative_path, file_path))
                    logger.debug(f"Found file: {file_path} (relative: {relative_path})")
        if self.filter_tree:
            directory_structure = files
        return files, directory_structure

    def combine_files(self) -> None:
        """
        Combine specified files into a single output file.
        """
        logger.debug(f"Combining files from directory: {self.directory} into output file: {self.output_file} with extensions: {self.extensions}")

        files, directory_structure = self.get_files_by_extension()

        folder_count = len(set(os.path.dirname(fp[0]) for fp in files))
        file_count = len(files)

        print(f"Found {Fore.CYAN}{folder_count}{Style.RESET_ALL} folders and {Fore.CYAN}{file_count}{Style.RESET_ALL} files with extensions {Fore.CYAN}{', '.join(self.extensions) if self.extensions != '*' else '*'}{Style.RESET_ALL} and matching patterns.")

        proceed = 'y'
        if '-y' not in sys.argv and '--skip-input' not in sys.argv:
            proceed = input(f"   Do you want to continue? (y/n): ")
        if proceed.lower() != 'y':
            print(f"{Fore.RED}Operation cancelled by user.{Style.RESET_ALL}")
            sys.exit(0)

        with open(self.output_file, 'w') as outfile:
            outfile.write(HEADER_MD)
            logger.debug(f"Writing header to {self.output_file}")

            # List the directory structure
            if self.tree:
                outfile.write("Directory structure and file locations are listed below:")
                for rel_path in directory_structure:
                    outfile.write(f"- `{rel_path}`\n")
                    logger.debug(f"Writing file path to {self.output_file}: {rel_path}")

            outfile.write("\n" + "-" * 79 + "\n")

            # Write the content of each file
            for idx, (rel_path, full_path) in enumerate(files, start=1):
                print(f"Processing ({Fore.GREEN}{idx}{Style.RESET_ALL}/{Fore.GREEN}{file_count}{Style.RESET_ALL}) {Fore.LIGHTBLACK_EX}{rel_path}{Style.RESET_ALL}")
                outfile.write(f"\n## `{rel_path}`\n")
                outfile.write("```python\n" if full_path.endswith('.py') else "```\n")
                with open(full_path, 'r') as infile:
                    content = infile.read()
                    logger.debug("Base Content \n", content, '\n ------------ \n')
                    content = self.remove_copyright(content)
                    logger.debug("No Copy Mode length \n", len(content))
                    if self.compact_mode:
                        content = self.remove_docstrings(content)
                        logger.debug("Compact Mode length \n", len(content))
                    outfile.write(content + "\n")
                    logger.debug(f"DEBUG: Writing content of {full_path} to {self.output_file}")
                outfile.write("```\n")

        print(f"{Fore.GREEN}Combined file is saved to {Fore.CYAN}{os.path.abspath(self.output_file)}{Style.RESET_ALL}")
        logger.debug(f"DEBUG: Combined file is saved to {os.path.abspath(self.output_file)}")

    @staticmethod
    def remove_copyright(content: str) -> str:
        """
        Remove copyright statements from the content.

        :param content: The content from which to remove copyright statements.
        :return: Content without copyright statements.
        """
        lines = content.split('\n')
        non_copyright_lines = []
        skip_lines = True
        inside_copyright = False

        for line in lines:
            # Check for the start of the copyright block
            if line.startswith('#  Copyright'):
                inside_copyright = True
                continue
            # Check for the end of the copyright block
            if inside_copyright and (line.strip() == '' or line.startswith('#')):
                continue
            else:
                inside_copyright = False

            # Add non-copyright lines
            if not inside_copyright:
                non_copyright_lines.append(line)

        return '\n'.join(non_copyright_lines)

    @staticmethod
    def remove_docstrings(content: str) -> str:
        """
        Remove docstrings from Python content.

        :param content: The content from which to remove docstrings.
        :return: Content without docstrings.
        """
        def replacer(match):
            return match.groups()[0] + match.groups()[-1]

        # Remove triple-quoted docstrings
        content = re.sub(r'(\s*(def|class)\s+\w+\s*\(.*?\):\s*\n\s*)("""[\s\S]*?""")(\s*)', replacer, content, flags=re.DOTALL)
        return content

    @staticmethod
    def print_usage() -> None:
        """
        Print the usage text for the script.
        """
        print(USAGE_TEXT)

    @classmethod
    def from_argv(cls) -> 'FileCombiner':
        """
        Create an instance from command line arguments.

        :return: An instance of FileCombiner.
        """
        test_mode = '--test-mode' in sys.argv
        compact_mode = '--compact-mode' in sys.argv
        tree = True
        filter_tree = False
        extensions = ['.py']
        include_patterns = []
        exclude_patterns = []

        if '-h' in sys.argv or '--help' in sys.argv:
            cls.print_usage()
            sys.exit(1)

        source_directory = os.getcwd()
        output_file = 'combined_file.md'

        # Parsing arguments
        in_args = sys.argv[1:]

        for d_check in ['--debug-mode']:
            if d_check in in_args:
                debug = True
                logger.setLevel("DEBUG")
            else:
                debug = False

        args = []
        for idx, arg in enumerate(in_args):
            if arg.startswith('-'):
                args.append(arg)
            elif arg.strip().startswith('['):
                full_arg = ''
                while_idx = idx
                while True:
                    if while_idx == len(in_args):
                        break
                    elif in_args[while_idx].strip().endswith(']'):
                        full_arg += in_args[while_idx]
                        break
                    else:
                        full_arg += in_args[while_idx]
                        while_idx += 1
                full_arg.strip().replace(" ", '')
                args.append(full_arg)

        if args:
            if not args[0].startswith('-'):
                output_file = args.pop(0)

        for arg in args:
            if arg.startswith('-'):
                if arg in ['-y', '--skip-input']:
                    proceed = 'y'
                elif arg in ['--all-files']:
                    extensions = '*'
                elif arg in ['--include-file-name']:
                    include_patterns = args[args.index(arg) + 1].strip('[]').split(',')
                    logger.debug(f"Include file name: {args[args.index(arg) + 1].strip('[]').split(',')} | {args} | {include_patterns}")
                elif arg in ['--exclude-file-name']:
                    exclude_patterns = args[args.index(arg) + 1].strip('[]').split(',')
                    logger.debug(f"Exclude file name: {args[args.index(arg) + 1].strip('[]').split(',')} | {args} | {exclude_patterns}")
                elif arg in ['--include-ext']:
                    extensions = args[args.index(arg) + 1].strip('[]').split(',')
                    logger.debug(f"Extensions: {args[args.index(arg) + 1].strip('[]').split(',')} | {args} | {extensions}")
                elif arg in ['--no-tree']:
                    tree = False
                elif arg in ['--filter-tree']:
                    filter_tree = True
                else:
                    print(f"{Fore.RED}{Style.BRIGHT}ERROR: {Style.RESET_ALL}invalid argument {Fore.YELLOW}{Style.BRIGHT}{arg}{Style.RESET_ALL} refer to help using {Fore.CYAN}{Style.BRIGHT} combine-files -h {Style.RESET_ALL}")
                    print_help = input("   Do you want to print help now? (y/n) :")
                    if Maybe(print_help).lower().out() == 'y':
                        cls.print_usage()
                    sys.exit(1)

        return cls(source_directory, output_file, extensions,
                   compact_mode, include_patterns, exclude_patterns, debug, tree, filter_tree)

    def run(self) -> None:
        """
        Run the file combiner process.
        """
        bool_colors = [
            f'{Fore.RED}{self.compact_mode}{Style.RESET_ALL}' if not self.compact_mode else f'{Fore.GREEN}{self.compact_mode}{Style.RESET_ALL}',
            f'{Fore.RED}{self.debug}{Style.RESET_ALL}' if not self.debug else f'{Fore.GREEN}{self.debug}{Style.RESET_ALL}',
            f'{Fore.RED}{self.tree}{Style.RESET_ALL}' if not self.tree else f'{Fore.GREEN}{self.tree}{Style.RESET_ALL}',
            f'{Fore.RED}{self.filter_tree}{Style.RESET_ALL}' if not self.filter_tree else f'{Fore.GREEN}{self.filter_tree}{Style.RESET_ALL}'
        ]

        print(f"""
{Fore.CYAN}{Style.BRIGHT}----Settings----{Style.RESET_ALL}
{Style.BRIGHT}Directories:{Style.RESET_ALL}
   Source directory: {Fore.CYAN}{self.directory}{Style.RESET_ALL}
   Output file: {Fore.CYAN}{os.path.abspath(self.output_file)}{Style.RESET_ALL}
{Style.BRIGHT}File Tree:{Style.RESET_ALL}
   Show File-Tree: {bool_colors[2]}
   Apply name filters to file tree: {bool_colors[3]}
{Style.BRIGHT}Filters:{Style.RESET_ALL}
   Included File Extensions: {Fore.YELLOW}{', '.join(self.extensions) if self.extensions != '*' else '*'}{Style.RESET_ALL}
   Include file name patterns: {Fore.YELLOW}{', '.join(self.include_patterns) if self.include_patterns else ''}{Style.RESET_ALL}
   Exclude file name patterns: {Fore.YELLOW}{', '.join(self.exclude_patterns) if self.exclude_patterns else ''}{Style.RESET_ALL}
{Style.BRIGHT}States:{Style.RESET_ALL}
   Compact mode: {bool_colors[0]}
   Debug mode: {bool_colors[1]}
{Fore.CYAN}----------------{Style.RESET_ALL}
""")

        if '-t' in sys.argv or '--test-mode' in sys.argv:
            print(f"{Fore.CYAN}Test mode: The script will only list the number of files and their paths.{Style.RESET_ALL}")
            # Test mode, only list the number of files and their paths
            files, _ = self.get_files_by_extension()
            print(f"Found {Fore.CYAN}{len(files)}{Style.RESET_ALL} files in \n{Fore.LIGHTBLACK_EX}{self.directory}{Style.RESET_ALL}:")
            for rel_path, full_path in files:
                print(f"    {Fore.LIGHTBLACK_EX}{rel_path}{Style.RESET_ALL}")
            sys.exit(0)

        self.combine_files()

def main() -> None:
    combiner = FileCombiner.from_argv()
    combiner.run()

