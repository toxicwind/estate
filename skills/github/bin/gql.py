#!/usr/bin/env python3
"""GraphQL helper for the GitHub skill: read pins, pin/unpin repos."""
import json
import os
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dynamic_credentials as dc

ALLOWED = ["*"]
CRED = "custom.github"


def gql(query, variables=None):
    payload = {"query": query, "variables": variables or {}}
    data = json.dumps(payload).encode()
    req = urllib.request.Request("https://api.github.com/graphql", data=data, method="POST")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "muse-github-skill")
    req.add_header("Content-Type", "application/json")
    dc.add_surrogate_to_request(req, CRED, allowed_hosts=ALLOWED)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return dc.read_json_response(resp)


PINS_Q = """
query($login: String!) {
  repositoryOwner(login: $login) {
    ... on User {
      pinnedItems(first: 6, types: REPOSITORY) {
        nodes {
          ... on Repository {
            id
            nameWithOwner
            description
            isPrivate
            isArchived
            pushedAt
            stargazerCount
          }
        }
      }
    }
  }
}
"""

PIN_M = """
mutation($repoId: ID!) {
  pinRepository(input: {repositoryId: $repoId}) {
    pinnedRepository { nameWithOwner }
  }
}
"""

UNPIN_M = """
mutation($repoId: ID!) {
  unpinRepository(input: {repositoryId: $repoId}) {
    clientMutationId
  }
}
"""

REPO_ID_Q = """
query($owner: String!, $name: String!) {
  repository(owner: $owner, name: $name) {
    id
    nameWithOwner
    description
    isPrivate
    isArchived
    pushedAt
    stargazerCount
  }
}
"""


def main(argv):
    cmd = argv[1] if len(argv) > 1 else "pins"
    if cmd == "pins":
        login = argv[2] if len(argv) > 2 else "toxicwind"
        print(json.dumps(gql(PINS_Q, {"login": login}), indent=1))
    elif cmd == "repoid":
        owner, name = argv[2].split("/", 1)
        print(json.dumps(gql(REPO_ID_Q, {"owner": owner, "name": name}), indent=1))
    elif cmd == "pin":
        print(json.dumps(gql(PIN_M, {"repoId": argv[2]}), indent=1))
    elif cmd == "unpin":
        print(json.dumps(gql(UNPIN_M, {"repoId": argv[2]}), indent=1))
    else:
        sys.exit("usage: gql.py pins [login] | repoid owner/repo | pin <repoId> | unpin <repoId>")


if __name__ == "__main__":
    main(sys.argv)
