import argparse
import os
import sys
from typing import Any, Callable, List

import tabulate

from determined_common import api
from determined_common.check import check_false

from . import render
from .declarative_argparse import Arg, Cmd, Group
from .user import authentication_required


def local_id(address: str) -> str:
    return os.path.basename(address)


@authentication_required
def list_agents(args: argparse.Namespace) -> None:
    r = api.get(args.master, "agents")

    agents = r.json()
    headers = ["Agent Name", "Registered Time", "Slots", "Label"]
    values = [
        [
            local_id(agent_id),
            render.format_time(agent["registered_time"]),
            len(agent["slots"]),
            agent["label"],
        ]
        for agent_id, agent in sorted(agents.items())
    ]

    print(tabulate.tabulate(values, headers, tablefmt="presto"), flush=False)


@authentication_required
def list_slots(args: argparse.Namespace) -> None:
    task_res = api.get(args.master, "tasks")
    agent_res = api.get(args.master, "agents")

    agents = agent_res.json()
    tasks = task_res.json()

    cont_names = {}
    for task in tasks.values():
        for cont in task["containers"]:
            cont_names[cont["id"]] = {"name": task["name"], "id": task["id"]}

    headers = ["Agent Name", "Slot ID", "Enabled", "Task ID", "Task Name", "Type", "Device"]
    values = [
        [
            local_id(agent_id),
            local_id(slot_id),
            slot["enabled"],
            cont_names[slot["container"]["id"]]["id"] if slot["container"] else "FREE",
            cont_names[slot["container"]["id"]]["name"] if slot["container"] else "None",
            slot["device"]["type"],
            slot["device"]["brand"],
        ]
        for agent_id, agent in sorted(agents.items())
        for slot_id, slot in sorted(agent["slots"].items())
    ]

    print(tabulate.tabulate(values, headers, tablefmt="presto"), flush=False)


def patch_agent(enabled: bool) -> Callable[[argparse.Namespace], None]:
    @authentication_required
    def patch(args: argparse.Namespace) -> None:
        check_false(args.all and args.agent_id)

        if not (args.all or args.agent_id):
            print("Error: must specify exactly one of `--all` or agent_id")
            sys.exit(1)

        if args.agent_id:
            agent_ids = [args.agent_id]
        else:
            r = api.get(args.master, "agents")
            agent_ids = sorted(local_id(a) for a in r.json().keys())

        for agent_id in agent_ids:
            path = "agents/{}/slots".format(agent_id)
            headers = {"Content-Type": "application/merge-patch+json"}
            payload = {"enabled": enabled}

            api.patch(args.master, path, body=payload, headers=headers)
            status = "Disabled" if not enabled else "Enabled"
            print("{} agent {}".format(status, agent_id))

    return patch


def patch_slot(enabled: bool) -> Callable[[argparse.Namespace], None]:
    @authentication_required
    def patch(args: argparse.Namespace) -> None:
        path = "agents/{}/slots/{}".format(args.agent_id, args.slot_id)
        headers = {"Content-Type": "application/merge-patch+json"}
        payload = {"enabled": enabled}

        api.patch(args.master, path, body=payload, headers=headers)
        status = "Disabled" if not enabled else "Enabled"
        print("{} slot {} of agent {}".format(status, args.slot_id, args.agent_id))

    return patch


def agent_id_completer(_1: str, parsed_args: argparse.Namespace, _2: Any) -> List[str]:
    r = api.get(parsed_args.master, "agents")
    return list(r.json().keys())


# fmt: off

args_description = [
    Cmd("a|gent", None, "manage agents", [
        Cmd("list", list_agents, "list agents", [], is_default=True),
        Cmd("enable", patch_agent(True), "enable agent", [
            Group(
                Arg("agent_id", help="agent ID", nargs="?", completer=agent_id_completer),
                Arg("--all", action="store_true", help="enable all agents"),
            )
        ]),
        Cmd("disable", patch_agent(False), "disable agent", [
            Group(
                Arg("agent_id", help="agent ID", nargs="?", completer=agent_id_completer),
                Arg("--all", action="store_true", help="disable all agents"),
            )
        ]),
    ]),
    Cmd("s|lot", None, "manage slots", [
        Cmd("list", list_slots, "list slots in cluster", [], is_default=True),
        Cmd("enable", patch_slot(True), "enable slot on agent", [
            Arg("agent_id", help="agent ID", completer=agent_id_completer),
            Arg("slot_id", type=int, help="slot ID"),
        ]),
        Cmd("disable", patch_slot(False), "disable slot on agent", [
            Arg("agent_id", help="agent ID", completer=agent_id_completer),
            Arg("slot_id", type=int, help="slot ID")
        ]),
    ]),
]  # type: List[Any]

# fmt: on
