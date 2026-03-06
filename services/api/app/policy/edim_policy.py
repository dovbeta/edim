from typing import List, Protocol


class Policy(Protocol):
    @property
    def role_name(self) -> str:
        ...

    @property
    def permissions(self) -> List[str]:
        ...

    @property
    def forbidden(self) -> List[str]:
        ...

    def to_str(self) -> str:
        ...


class BasePolicy:
    def __init__(self, role_name: str, permissions: List[str], forbidden: List[str]):
        self._role_name = role_name
        self._permissions = permissions
        self._forbidden = forbidden

    @property
    def role_name(self) -> str:
        return self._role_name

    @property
    def permissions(self) -> List[str]:
        return self._permissions

    @property
    def forbidden(self) -> List[str]:
        return self._forbidden

    def to_str(self) -> str:
        res = f"{self.role_name.capitalize()} permissions:\n"
        for p in self.permissions:
            res += f"- {p}\n"
        if self.forbidden:
            res += "\nForbidden:\n"
            for f in self.forbidden:
                res += f"- {f}\n"
        return res


class ResidentPolicy(BasePolicy):
    def __init__(self):
        super().__init__(
            role_name="resident",
            permissions=[
                "May access contact of specific apartment owner",
                "May access contact by vehicle plate",
                "May access neighbor in same building",
                "Only targeted lookup allowed",
            ],
            forbidden=[
                "list of residents",
                "list of vehicles",
                "bulk contacts",
            ]
        )


class BoardPolicy(BasePolicy):
    def __init__(self):
        super().__init__(
            role_name="board",
            permissions=[
                "Full access to residents of organization",
                "May list residents",
                "May list vehicles",
                "May access contacts",
                "May aggregate statistics",
            ],
            forbidden=[]
        )


class EDIMAccessPolicy:
    @staticmethod
    def resolve_role(context: dict) -> str:
        org_roles = context.get("org_roles", [])

        for r in org_roles:
            if r.get("role") == "board":
                return "board"

        return "resident"

    @staticmethod
    def get_policy(role: str) -> Policy:
        if role == "board":
            return BoardPolicy()
        return ResidentPolicy()

    @staticmethod
    def rules_for(role: str) -> str:
        return EDIMAccessPolicy.get_policy(role).to_str()
