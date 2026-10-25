"""发布前明确拒绝占位模板、占位维护者和未匹配的版本标签；不上传任何内容。"""

import argparse

from project_metadata import metadata


def validate(config, version, tag):
    project = config["project"]
    if project["name"].lower().replace("_", "-").replace(".", "-") == "example":
        raise ValueError("占位模板禁止上传PyPI，请先改名")
    if not project.get("authors") or any(
        not a.get("name", "").strip()
        or a.get("name", "").strip().lower() == "your name"
        or a.get("email", "").lower() == "you@example.com"
        for a in project["authors"]
    ):
        raise ValueError("发布前必须替换维护者占位信息")
    if not project.get("urls") or any(
        "github.com/guyue55/py_example" in url.lower() for url in project["urls"].values()
    ):
        raise ValueError("发布前必须更新项目链接")
    if tag != "v" + version:
        raise ValueError("发布标签与源码版本不一致")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag", required=True)
    args = parser.parse_args()
    config, _, version = metadata()
    validate(config, version, args.tag)
    print("RELEASE_PREFLIGHT_OK", version)


if __name__ == "__main__":
    main()
