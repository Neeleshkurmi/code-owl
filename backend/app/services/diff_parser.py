import re


class DiffParser:

    @staticmethod
    def get_changed_lines(diff: str) -> dict[str, set[int]]:
        changed_lines: dict[str, set[int]] = {}

        current_file = None
        current_new_line = None

        for line in diff.splitlines():

            if line.startswith("+++ b/"):
                current_file = line[6:]
                changed_lines[current_file] = set()
                continue

            if line.startswith("@@"):
                match = re.search(
                    r"\+(\d+)(?:,(\d+))?",
                    line,
                )

                if match:
                    current_new_line = int(match.group(1))

                continue

            if current_file is None or current_new_line is None:
                continue

            if line.startswith("+") and not line.startswith("+++"):
                changed_lines[current_file].add(
                    current_new_line
                )
                current_new_line += 1

            elif line.startswith("-") and not line.startswith("---"):
                # Deleted line: it doesn't exist on RIGHT side.
                continue

            else:
                # Context line
                current_new_line += 1

        return changed_lines