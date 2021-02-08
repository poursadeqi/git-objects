import subprocess
import os
import argparse
import json


def get_file_content(file_path):
    with open(file_path) as f:
        return f.read()


def get_object_type(object_id):
    result = subprocess.run(['git', '-C', base_path, 'cat-file', '-t', object_id], stdout=subprocess.PIPE)
    return result.stdout.decode('utf-8').rstrip()


def get_children_from_commit(object_id):
    lines = get_content_of_object(object_id)
    sha = lines[0].split(' ')[1]
    commit_message = lines[-1]
    return {
        'id': sha,
        'type': get_object_type(sha),
        'parent_label': commit_message,
        'children': get_object(sha)
    }


def get_children_from_tree(object_id):
    lines = get_content_of_object(object_id)

    result = []
    for line in lines:
        line_splitted = line.split(" ")
        sha = line_splitted[-1].split('\t')[0]
        commit_message = line_splitted[-1].split('\t')[1]

        obj = {
            'type': get_object_type(sha),
            'id': sha,
            'label': commit_message,
        }

        if obj['type'] != 'blob':
            obj['children'] = get_object(sha)

        result.append(obj)
    return result


def get_content_of_object(object_id):
    result = subprocess.run(['git', '-C', base_path, 'cat-file', '-p', object_id], stdout=subprocess.PIPE)
    content = result.stdout.decode('utf-8').rstrip()
    lines = content.split("\n")
    return lines


def get_object(sha):
    result = {'id': sha, 'type': get_object_type(sha)}

    if result['type'] == 'blob':
        result['content'] = get_content_of_object(sha)
        return result

    if result['type'] == 'commit':
        children = get_children_from_commit(sha)
        result['label'] = children['parent_label']
        result['children'] = children['children']

        return result

    if result['type'] == 'tree':
        result['children'] = get_children_from_tree(sha)
        return result


def get_tree_from_objects(objects_path):
    tree_obj = {}

    with os.scandir(objects_path) as obj_path:
        for obj_parent in obj_path:
            if obj_parent.is_dir():
                with os.scandir(obj_parent.path) as obj_children:
                    for obj_child in obj_children:
                        sha = obj_parent.name + obj_child.name
                        current = get_object(sha)
                        tree_obj[sha] = current

    return tree_obj


def print_output(output, prettify=False):
    indent = 4 if prettify == 'T' else None
    print(json.dumps(output, indent=indent))


# Parse arguments

parser = argparse.ArgumentParser()
parser.add_argument('-p', '--path', metavar='path', required=True, help='Path of the repository')
parser.add_argument('--pretty', metavar='pretty', required=False, default=False, help='Prettify the output values: T/F')
args = parser.parse_args()

# Get tree
base_path = args.path

branches_path = base_path + '/.git/refs/heads'
objects_path = base_path + '/.git/objects/'

tree = get_tree_from_objects(objects_path)

# Print it out
print_output(tree, args.pretty)