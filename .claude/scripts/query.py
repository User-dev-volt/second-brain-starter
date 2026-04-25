"""
query.py — Unified CLI for all Second Brain integrations.

Usage:
  python query.py github activity [--days N] [--json]
  python query.py github issues --repo <name> [--json]

  python query.py comfyui queue
  python query.py comfyui recent [--limit N]
  python query.py comfyui submit <workflow.json>
  python query.py comfyui watch

  python query.py obsidian daily <text> [--prefix TAG]
  python query.py obsidian snapshot <slug> [Key=Value ...]
  python query.py obsidian context <slug>
  python query.py obsidian index
  python query.py obsidian idea <text> [--project NAME]
  python query.py obsidian learning <text> [--category CATEGORY]

  python query.py assets log --filename <f> [--workflow W] [--prompt P] [--notes N] [--tags T ...]
  python query.py assets search <query>
  python query.py assets list [--limit N]
"""

import sys
import json
import argparse
from pathlib import Path

# Add integrations to path
_HERE = Path(__file__).parent
sys.path.insert(0, str(_HERE / "integrations"))
sys.path.insert(0, str(_HERE / "utils"))


def cmd_github(args):
    import github_integration as gh

    client = gh.authenticate()

    if args.github_cmd == "activity":
        data = gh.get_recent_activity(client, days=args.days)
        if args.as_json:
            print(json.dumps(data, indent=2))
        else:
            print(gh.format_context(data))

    elif args.github_cmd == "issues":
        data = gh.get_open_issues(client, args.repo)
        if args.as_json:
            print(json.dumps(data, indent=2))
        else:
            for i in data:
                kind = "PR" if i["is_pr"] else "Issue"
                labels = ", ".join(i["labels"]) or "no labels"
                print(f"  [{kind} #{i['number']}] {i['title']} ({labels})")


def cmd_comfyui(args):
    import comfyui_integration as comfy

    if args.comfy_cmd == "queue":
        print(json.dumps(comfy.get_queue_status(), indent=2))

    elif args.comfy_cmd == "recent":
        items = comfy.get_recent_outputs(args.limit)
        print(f"{len(items)} recent outputs:")
        for item in items:
            outputs = item.get("outputs", {})
            for node_id, node_out in outputs.items():
                for img in node_out.get("images", []):
                    print(f"  {img.get('filename')} ({img.get('type')})")

    elif args.comfy_cmd == "submit":
        workflow = json.loads(Path(args.workflow_file).read_text(encoding="utf-8"))
        prompt_id = comfy.submit_workflow(workflow)
        print(f"Submitted: {prompt_id}")
        result = comfy.poll_result(prompt_id)
        print(json.dumps(result, indent=2))

    elif args.comfy_cmd == "watch":
        comfy.watch_via_websocket()


def cmd_obsidian(args):
    import obsidian

    if args.obs_cmd == "daily":
        path = obsidian.append_to_daily(args.text, args.prefix)
        print(f"Appended to {path}")

    elif args.obs_cmd == "snapshot":
        fields = dict(kv.split("=", 1) for kv in args.fields)
        path = obsidian.update_project_snapshot(args.slug, fields)
        print(f"Updated {path}")

    elif args.obs_cmd == "context":
        ctx = obsidian.get_project_context(args.slug)
        print(ctx or f"No snapshot found for '{args.slug}'")

    elif args.obs_cmd == "index":
        path = obsidian.update_project_index()
        print(f"Rebuilt {path}")

    elif args.obs_cmd == "idea":
        path = obsidian.capture_idea(args.text, args.project)
        print(f"Idea saved to {path}")

    elif args.obs_cmd == "learning":
        path = obsidian.log_learning(args.text, args.category)
        print(f"Learning saved to {path}")


def cmd_assets(args):
    import asset_cataloger as ac

    if args.asset_cmd == "log":
        entry = ac.log_asset(
            filename=args.filename,
            workflow=args.workflow,
            prompt=args.prompt,
            notes=args.notes,
            dest_path=args.dest,
            tags=args.tags,
        )
        print(f"Logged: {entry['filename']} on {entry['date']}")

    elif args.asset_cmd == "search":
        results = ac.search_assets(args.query)
        if not results:
            print(f"No assets matching '{args.query}'")
        else:
            for e in results:
                print(f"  [{e['date']}] {e['filename']}")
                if e.get("prompt"):
                    print(f"    Prompt: {e['prompt'][:80]}")

    elif args.asset_cmd == "list":
        assets = ac.list_assets(args.limit)
        for e in assets:
            print(f"  [{e['date']}] {e['filename']}")


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Second Brain unified query interface",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    top = parser.add_subparsers(dest="integration")

    # --- GitHub ---
    gh = top.add_parser("github", help="GitHub integration")
    gh_sub = gh.add_subparsers(dest="github_cmd")

    gh_act = gh_sub.add_parser("activity")
    gh_act.add_argument("--days", type=int, default=7)
    gh_act.add_argument("--json", action="store_true", dest="as_json")

    gh_iss = gh_sub.add_parser("issues")
    gh_iss.add_argument("--repo", required=True)
    gh_iss.add_argument("--json", action="store_true", dest="as_json")

    # --- ComfyUI ---
    cf = top.add_parser("comfyui", help="ComfyUI integration")
    cf_sub = cf.add_subparsers(dest="comfy_cmd")

    cf_sub.add_parser("queue")

    cf_rec = cf_sub.add_parser("recent")
    cf_rec.add_argument("--limit", type=int, default=10)

    cf_sub_p = cf_sub.add_parser("submit")
    cf_sub_p.add_argument("workflow_file")

    cf_sub.add_parser("watch")

    # --- Obsidian ---
    ob = top.add_parser("obsidian", help="Obsidian vault operations")
    ob_sub = ob.add_subparsers(dest="obs_cmd")

    ob_d = ob_sub.add_parser("daily")
    ob_d.add_argument("text")
    ob_d.add_argument("--prefix", default="")

    ob_s = ob_sub.add_parser("snapshot")
    ob_s.add_argument("slug")
    ob_s.add_argument("fields", nargs="*", help="Key=Value pairs")

    ob_c = ob_sub.add_parser("context")
    ob_c.add_argument("slug")

    ob_sub.add_parser("index")

    ob_i = ob_sub.add_parser("idea")
    ob_i.add_argument("text")
    ob_i.add_argument("--project", default="")

    ob_l = ob_sub.add_parser("learning")
    ob_l.add_argument("text")
    ob_l.add_argument("--category", default="general")

    # --- Assets ---
    ass = top.add_parser("assets", help="Asset catalog")
    ass_sub = ass.add_subparsers(dest="asset_cmd")

    ass_log = ass_sub.add_parser("log")
    ass_log.add_argument("--filename", required=True)
    ass_log.add_argument("--workflow", default="")
    ass_log.add_argument("--prompt", default="")
    ass_log.add_argument("--notes", default="")
    ass_log.add_argument("--dest", default="")
    ass_log.add_argument("--tags", nargs="*", default=[])

    ass_search = ass_sub.add_parser("search")
    ass_search.add_argument("query")

    ass_list = ass_sub.add_parser("list")
    ass_list.add_argument("--limit", type=int, default=20)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    if args.integration == "github":
        cmd_github(args)
    elif args.integration == "comfyui":
        cmd_comfyui(args)
    elif args.integration == "obsidian":
        cmd_obsidian(args)
    elif args.integration == "assets":
        cmd_assets(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
