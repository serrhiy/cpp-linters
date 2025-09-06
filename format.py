#!/usr/bin/env python3

import sys, os, shutil, argparse, subprocess, pathlib

CPP_EXTENSIONS = {
  '.cpp', '.cc', '.cxx', '.C',
  '.h', '.hpp', '.hh', '.hxx',
  '.ipp', '.tpp', '.inl'
}

def print_to_stderr(*args, **kwargs):
  print(*args, file=sys.stderr, **kwargs)

def find_format_file() -> str:
  search_path = pathlib.Path(os.getcwd())
  files = tuple(search_path.rglob('.clang-format'))
  if len(files) == 0:
    raise Exception('Could not find .clang-format file')
  if len(files) > 1:
    raise Exception('Finded multiple .clang-format files')
  return str(files[0].resolve())

def extract_cpp_specified_files(search_paths: set[str], ignore_paths: set[str]) -> set[str]:
  return set({ path for path in search_paths
                if os.path.isfile(path) and path not in ignore_paths })

def extract_specified_folders(search_paths: set[str], ignore_paths: set[str]) -> set[str]:
  return set({ path for path in search_paths
                if os.path.isdir(path) and path not in ignore_paths })

def get_cpp_files_from_folder(folder, ignore_paths: set[str]) -> set[str]:
  cpp_files: set[str] = set()
  for root, _, files in os.walk(folder):
    if root in ignore_paths:
      continue
    
    for filename in files:
      _, file_extention = os.path.splitext(filename)
      fullpath = os.path.join(root, filename)
      if file_extention not in CPP_EXTENSIONS or fullpath in ignore_paths:
        continue
      cpp_files.add(fullpath)

  return cpp_files

def get_cpp_file_names(search_paths: list[str], ignore_paths: list[str]):
  absolute_search_paths = { os.path.abspath(path) for path in search_paths }
  absolute_ignore_paths = { os.path.abspath(path) for path in ignore_paths }

  cpp_files = extract_cpp_specified_files(absolute_search_paths, absolute_ignore_paths)
  folders = extract_specified_folders(absolute_search_paths.difference(cpp_files), absolute_ignore_paths)
  invalid_paths = absolute_search_paths.difference(cpp_files, folders)

  if len(invalid_paths) > 0:
    print_to_stderr(f'Invalid paths:\n{'\n'.join(invalid_paths)}')

  for folder in folders:
    cpp_files.update(get_cpp_files_from_folder(folder, absolute_ignore_paths))

  return cpp_files

def main(args):
  if shutil.which('clang-format') is None:
    raise Exception('clang-format is not installed')

  search_paths = args.path.split(',') if args.path is not None else ['.']
  ignore_paths = args.ignore.split(',') if args.ignore is not None else []

  cpp_files = get_cpp_file_names(search_paths, ignore_paths)

  subprocess.run(['clang-format', f'-style=file:{find_format_file()}', '-i', *cpp_files], check=True)

if __name__ == '__main__':
  try:
    parser = argparse.ArgumentParser(
      prog='format',
      description='Format c++ files using clang-format'
    )
    parser.add_argument('-i', '--ignore')
    parser.add_argument('-p', '--path')
    main(parser.parse_args())
  except Exception as exception:
    print_to_stderr(str(exception))
