
from NGIN.ai.lib.ngin_action import SimulaeAction
from NGIN.ai.lib.socialization_utils import _normalize_action_step, get_heuristic


class TaskPlan():
    """A goal with ordered pre-actions, a primary action, and post-actions."""

    def __init__(self, target, action, pre_actions=None, post_actions=None):
        self.target = target
        self.action = action
        self.pre_actions = list(pre_actions) if pre_actions else []
        self.post_actions = list(post_actions) if post_actions else []

        # Plans can be compared before execution, so we score the full chain
        # when the plan is created.
        self.heuristic = get_heuristic(self.all_actions(), target=target)

    def all_actions(self):
        """Return the remaining plan steps in execution order."""

        all = []
        
        if self.pre_actions:
            all.extend(
                step for step in (
                    _normalize_action_step(action, self.target)
                    for action in self.pre_actions
                )
                if step
            )

        normalized_action = _normalize_action_step(self.action, self.target)
        if normalized_action:
            all.append(normalized_action)

        if self.post_actions:
            all.extend(
                step for step in (
                    _normalize_action_step(action, self.target)
                    for action in self.post_actions
                )
                if step
            )

        return all
    
    def next_action(self):
        """Pop and return the next executable step."""
        
        if self.pre_actions:
            return _normalize_action_step(self.pre_actions.pop(0), self.target)
        
        if self.action:
            action = self.action
            self.action = None
            return _normalize_action_step(action, self.target)

        if self.post_actions:
            return _normalize_action_step(self.post_actions.pop(0), self.target)

        return None

    def is_complete(self):
        """True when the plan has no remaining work."""

        return not self.pre_actions and self.action is None and not self.post_actions

    def _describe_step(self, step):
        normalized = _normalize_action_step(step, self.target)

        if not normalized:
            return "<empty>"

        action, target = normalized
        action_name = action.name if isinstance(action, SimulaeAction) else str(action)
        return f"{action_name}({target})"
        

    def summary(self):
        """Return a readable multi-step plan description."""

        summary = str(self)
        summary += "\n\tActions: ["
        first = True
        for action in self.all_actions():
            summary += f"{'' if first else ', '}{self._describe_step(action)}"
            first = False
        summary += "]"
        return summary

    def __str__(self):
        return f"Task : [{self.heuristic}] for [{len(self.all_actions())} actions on {self.target}]"
