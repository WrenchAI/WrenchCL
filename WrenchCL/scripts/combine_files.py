import os
import sys
from colorama import Fore, Style, init
from ..Tools.WrenchLogger import Logger

logger = Logger()
init(autoreset=True)

HEADER_MD = """\
# Combined Files Reference

This is a combined file representative of a folder structure, only used as reference.
Directory structure and file locations are listed below:
"""

def get_files_by_extension(directory, extensions, avoid_file=None, debug=False):
    """Recursively get all files with specified extensions in the directory."""
    if debug:
        print(f"{Fore.LIGHTBLACK_EX}DEBUG: Scanning directory: {directory} for extensions: {extensions}{Style.RESET_ALL}")
    files = []
    for root, _, files_in_dir in os.walk(directory):
        for file in files_in_dir:
            if extensions == '*' or any(file.endswith(ext) for ext in extensions):
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, directory)
                if avoid_file and os.path.abspath(file_path) == os.path.abspath(avoid_file):
                    if debug:
                        print(f"{Fore.LIGHTBLACK_EX}DEBUG: Avoiding file: {file_path}{Style.RESET_ALL}")
                    continue
                files.append((relative_path, file_path))
                if debug:
                    print(f"{Fore.LIGHTBLACK_EX}DEBUG: Found file: {file_path} (relative: {relative_path}){Style.RESET_ALL}")
    return files

def combine_files(directory, output_file, extensions, debug=False):
    """Combine specified files into a single output file."""
    if debug:
        print(f"{Fore.LIGHTBLACK_EX}DEBUG: Combining files from directory: {directory} into output file: {output_file} with extensions: {extensions}{Style.RESET_ALL}")

    files = get_files_by_extension(directory, extensions, avoid_file=output_file, debug=debug)

    folder_count = len(set(os.path.dirname(fp[0]) for fp in files))
    file_count = len(files)

    print(f"Found {Fore.CYAN}{folder_count}{Style.RESET_ALL} folders and {Fore.CYAN}{file_count}{Style.RESET_ALL} files with extensions {Fore.CYAN}{', '.join(extensions) if extensions != '*' else '*'}{Style.RESET_ALL}.")
    if debug:
        print(f"{Fore.LIGHTBLACK_EX}DEBUG: Found {folder_count} folders and {file_count} files.{Style.RESET_ALL}")

    proceed = input(f"   Do you want to continue? (y/n): ")
    if proceed.lower() != 'y':
        print(f"{Fore.RED}Operation cancelled by user.{Style.RESET_ALL}")
        if debug:
            print(f"{Fore.LIGHTBLACK_EX}DEBUG: Operation cancelled by user.{Style.RESET_ALL}")
        sys.exit(0)

    with open(output_file, 'w') as outfile:
        outfile.write(HEADER_MD)
        if debug:
            print(f"{Fore.LIGHTBLACK_EX}DEBUG: Writing header to {output_file}{Style.RESET_ALL}")

        # List the directory structure
        for rel_path, _ in files:
            outfile.write(f"- `{rel_path}`\n")
            if debug:
                print(f"{Fore.LIGHTBLACK_EX}DEBUG: Writing file path to {output_file}: {rel_path}{Style.RESET_ALL}")

        outfile.write("\n" + "-" * 79 + "\n")

        # Write the content of each file
        for idx, (rel_path, full_path) in enumerate(files, start=1):
            print(f"Processing ({Fore.GREEN}{idx}{Style.RESET_ALL}/{Fore.GREEN}{file_count}{Style.RESET_ALL}) {Fore.LIGHTBLACK_EX}{rel_path}{Style.RESET_ALL}")
            if debug:
                print(f"{Fore.LIGHTBLACK_EX}DEBUG: Processing file {idx}/{file_count}: {full_path}{Style.RESET_ALL}")
            outfile.write(f"\n## `{rel_path}`\n")
            outfile.write("```python\n" if full_path.endswith('.py') else "```\n")
            with open(full_path, 'r') as infile:
                content = infile.read()
                outfile.write(content + "\n")
                if debug:
                    print(f"{Fore.LIGHTBLACK_EX}DEBUG: Writing content of {full_path} to {output_file}{Style.RESET_ALL}")
            outfile.write("```\n")

    print(f"{Fore.GREEN}Combined files are saved to {Fore.CYAN}{output_file}{Style.RESET_ALL}")
    if debug:
        print(f"{Fore.LIGHTBLACK_EX}DEBUG: Combined files are saved to {output_file}{Style.RESET_ALL}")

def print_usage():
    print(f"""
{Fore.GREEN}--- Combine Files ---{Style.RESET_ALL}

This script combines files from the current working directory into a single markdown file.
It's useful for sharing data with other developers or feeding it to Large Language Models (LLMs) for analysis or questions.

{Fore.YELLOW}Usage:{Style.RESET_ALL}
  combine-files [output_file] [extensions]

{Fore.YELLOW}Arguments:{Style.RESET_ALL}
  {Fore.YELLOW}--> Output file:{Style.RESET_ALL} Path to output file (default is 'combined_file.md')
  {Fore.YELLOW}--> Extensions:{Style.RESET_ALL} Comma-separated list of file extensions to include (e.g., '.py,.json'). Use '-all' or '-a' to include all files.

{Fore.CYAN}Commands:{Style.RESET_ALL}
  {Fore.CYAN}--> -h or --help:{Style.RESET_ALL} Prints this help message
  {Fore.CYAN}--> -y or --yes:{Style.RESET_ALL} Skips user input confirmation
  {Fore.CYAN}--> -t or --test:{Style.RESET_ALL} Test run, only lists number of files and paths it will combine
  {Fore.CYAN}--> -c or --copyright:{Style.RESET_ALL} Prints the copyright notice
  {Fore.CYAN}--> -d or --debug:{Style.RESET_ALL} Prints debug information step by step

{Fore.GREEN}Examples:{Style.RESET_ALL}
  combine-files -a Combines all Python files in the current directory and saves to 'combined_file.md'.
  combine-files ../combined_file.md -all -d - Combines all files in the current directory and saves to 'combined_file.md' with debug information.
  combine-files combined_file.md .py,.json - Combines all Python and JSON files in the current directory.
  combine-files combined_file.md .json.py -d - Combines all files with extensions .json and .py in the current directory with debug information.

{Fore.GREEN}----------------------------{Style.RESET_ALL}
""")

def main():
    test_mode = False
    debug = '-d' in sys.argv or '--debug' in sys.argv

    if debug:
        print(f"{Fore.RED} DEBUG MODE ACTIVE{Style.RESET_ALL}")

    if '-h' in sys.argv or '--help' in sys.argv:
        if debug:
            print(f"{Fore.YELLOW} Help command found{Style.RESET_ALL}")
        print_usage()
        sys.exit(1)

    source_directory = os.getcwd()
    output_file = '../combined_file.md'
    extensions = ['.py']

    # Parsing arguments
    args = sys.argv[1:]
    if args:
        if not args[0].startswith('-'):
            output_file = args.pop(0)
        if args and not args[0].startswith('-'):
            extensions = [ext.strip() for ext in args.pop(0).split(',')]

    for arg in args:
        if arg.startswith('-'):
            if arg in ['-y', '--yes']:
                proceed = 'y'
            elif arg in ['-t', '--test']:
                test_mode = True
            elif arg in ['-c', '--copyright']:
                print("Copyright (c) 2024. Willem van der Schans")
                print("MIT License")
                sys.exit(0)
            elif arg in ['-d', '--debug']:
                debug = True
            elif arg in ['-a', '--all']:
                extensions = '*'

    if os.path.exists(output_file) and output_file.split('.')[-1] in extensions:
        avoid = input(f"{Fore.YELLOW}The file {output_file} already exists. Do you want to avoid including it in the combined file? (y/n): {Style.RESET_ALL}")
        if avoid.lower() != 'y':
            print(f"{Fore.RED}Error: The file {output_file} already exists. Please choose a different output file.{Style.RESET_ALL}")
            sys.exit(1)

    print(f"""
{Fore.CYAN}----Settings----{Style.RESET_ALL}
   Source directory: {Fore.LIGHTBLACK_EX}{source_directory}{Style.RESET_ALL}
   Output file: {Fore.LIGHTBLACK_EX}{os.path.abspath(output_file)}{Style.RESET_ALL}
   Extensions: {Fore.LIGHTBLACK_EX}{', '.join(extensions) if extensions != '*' else '*'}{Style.RESET_ALL}
{Fore.CYAN}----------------{Style.RESET_ALL}
""")

    if test_mode:
        print(f"{Fore.CYAN}Test mode: The script will only list the number of files and their paths.{Style.RESET_ALL}")
        # Test mode, only list the number of files and their paths
        files = get_files_by_extension(source_directory, extensions, avoid_file=output_file, debug=debug)
        print(f"Found {Fore.CYAN}{len(files)}{Style.RESET_ALL} files in \n{Fore.LIGHTBLACK_EX}{source_directory}{Style.RESET_ALL}:")
        for rel_path, full_path in files:
            print(f"    {Fore.LIGHTBLACK_EX}{rel_path}{Style.RESET_ALL}")
        sys.exit(0)

    combine_files(source_directory, output_file, extensions, debug)

if __name__ == "__main__":
    main()
