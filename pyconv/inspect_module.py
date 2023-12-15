import dataclasses
import inspect
import os.path
import textwrap

MAIN_PACKAGE_NAME = "ansys.dpf.composites"
TAB_SIZE = 4


@dataclasses.dataclass
class Details:
    name: str
    package_path: str
    type: str  # make string enum
    members: dict
    documentation: str


def inspect_main_module(module):
    doc_string = ""
    members = inspect.getmembers(module)
    imports_from_all = []
    module_name = None
    for name, value in members:
        if name == "__all__":
            imports_from_all = list(value)
        elif name == "__name__":
            module_name = value

    if module_name is None:
        raise Exception("Module name not found!")

    print(f"Pressing module {module_name}: __all__ = {imports_from_all}")
    doc_string += f"{module_name}: {module.__doc__}\n"

    level = 1

    for name, value in members:
        if name in imports_from_all:
            if inspect.ismodule(value):
                doc_string = inspect_submodule(value, doc_string, level)
            elif inspect.isclass(value):
                doc_string = inspect_class(value, doc_string, level)
            elif inspect.isfunction(value):
                doc_string = document_function(value, doc_string, level)
            elif inspect.ismethod(value):
                doc_string = inspect_method(value, doc_string, level)
            elif isinstance(value, property):
                raise Exception("Property found! Not implemented on level module")

    return doc_string


def inspect_submodule(sub_module, doc_string, level):
    print("Submodule: ", sub_module)
    submodule_name = sub_module.__name__.split(".")[-1]
    doc_string += f"{' '*TAB_SIZE*level}Submodule {inspect.getmodule(sub_module).__package__}.{submodule_name}\n"
    doc_string += f"{' '*TAB_SIZE*(level+1)}Documentation:\n{textwrap.indent(sub_module.__doc__, ' '*TAB_SIZE*(level+1))}\n"
    members = inspect.getmembers(composites.composite_model)
    level += 1
    for name, value in members:
        if not name.startswith("_"):
            package_name = inspect.getmodule(value).__package__
            if package_name.startswith(MAIN_PACKAGE_NAME):
                print("   process ansys.dpf.composites submodule: ", submodule_name)
                if inspect.ismodule(value):
                    doc_string = inspect_submodule(value, doc_string, level)
                elif inspect.isclass(value):
                    doc_string = inspect_class(value, doc_string, level)
                elif inspect.isfunction(value):
                    doc_string = document_function(value, doc_string, level)
                elif inspect.ismethod(value):
                    doc_string = inspect_method(value, doc_string, level)
    return doc_string


def inspect_class(module_class, doc_string, level):
    package_name = inspect.getmodule(module_class).__package__
    if not package_name.startswith(MAIN_PACKAGE_NAME):
        return doc_string

    class_members = inspect.getmembers(module_class)
    class_name = module_class.__name__
    doc_string += f"{' ' * TAB_SIZE * level}Class {class_name}{inspect.signature(module_class)}\n"
    doc_string += f"{' ' * TAB_SIZE * (level + 1)}Documentation:\n{textwrap.indent(module_class.__doc__, ' ' * TAB_SIZE * (level + 1))}\n"

    level += 1
    for name, value in class_members:
        if not name.startswith("_"):
            if inspect.ismodule(value):
                raise Exception("Module found in class!")
            elif inspect.isclass(value):
                doc_string = inspect_class(value, doc_string, level)
            elif inspect.isfunction(value):
                doc_string = document_function(value, doc_string, level)
            elif inspect.ismethod(value):
                doc_string = inspect_method(value, doc_string, level)
            elif isinstance(value, property):
                doc_string = document_property(name, value.__doc__, doc_string, level)

    return doc_string


def document_function(member, doc_string, level):
    doc_string += f"{' ' * TAB_SIZE * level}Function {member.__name__}{inspect.signature(member)}\n"
    doc_string += f"{' ' * TAB_SIZE * (level + 1)}Documentation:\n{textwrap.indent(member.__doc__, ' ' * TAB_SIZE * (level + 1))}\n"
    return doc_string


def inspect_method(member, doc_string, level):
    print("Method: ", member)
    raise Exception("Method not implemented!")


def document_property(name, doc, doc_string, level):
    doc_string += f"{' ' * TAB_SIZE * level}Property {name}\n"
    doc_string += f"{' ' * TAB_SIZE * (level + 1)}Documentation:\n{textwrap.indent(doc, ' ' * TAB_SIZE * (level + 1))}\n"
    return doc_string


if __name__ == "__main__":
    import ansys.dpf.composites as composites

    doc_string = inspect_main_module(composites)
    dir = os.path.dirname(__file__)
    with open(os.path.join(dir, "documentation_plain_text.txt"), "w") as f:
        f.write(doc_string)
