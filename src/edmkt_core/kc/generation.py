# Ported from tcc.edm.kt — notebooks/03b_kc_generation.ipynb cell 8 (KC generation, Etapa 2).
# Frozen prompts (D-01 determinism) kept verbatim; the inline anthropic call is replaced by the
# injected LLMClient.generate(system, prompt, schema) (DIP, KC-01). The notebook's markdown-fence
# parsing is dropped from the core primary path — the app transport handles structured output.

from __future__ import annotations

from edmkt_core.kc.ports import LLMClient


class EmptyKCError(ValueError):
    """A problem yielded 0 KCs (KC-04 0-KC guard, defense-in-depth over schema minItems:1)."""


# JSON Schema for --json-schema (RESEARCH §Code Examples). minItems:1 encodes ≥1 KC/problem at
# the transport; EmptyKCError below re-checks it in-core (the CLI may not fill structured_output).
KC_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "problem_description": {"type": "string"},
        "kcs": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "reasoning": {"type": "string"},
                },
                "required": ["name", "reasoning"],
            },
        },
    },
    "required": ["problem_description", "kcs"],
}

# In-context examples adapted from Duan et al. (2025), Appendix B (Table 8): two intro Java
# problems anchoring KC naming (3-8 words) and granularity (3-7 KCs/problem).
_FEW_SHOT_EXAMPLES = """\
=== FEW-SHOT EXAMPLE 1 ===
Problem A — Correct student solutions (n=3):

Solution 1:
```java
public static int sumArray(int[] arr) {
    int total = 0;
    for (int i = 0; i < arr.length; i++) {
        total += arr[i];
    }
    return total;
}
```
Solution 2:
```java
public static int sumArray(int[] arr) {
    int sum = 0;
    for (int num : arr) {
        sum += num;
    }
    return sum;
}
```
Solution 3:
```java
public static int sumArray(int[] numbers) {
    int result = 0;
    int i = 0;
    while (i < numbers.length) {
        result += numbers[i];
        i++;
    }
    return result;
}
```
Expected JSON output:
{
  "problem_description": "Compute the sum of all integer elements in an array and return the total.",
  "kcs": [
    {"name": "Array traversal with loop", "reasoning": "All solutions iterate through every element using index-based for, enhanced for-each, or while loops."},
    {"name": "Accumulator variable pattern", "reasoning": "Each solution initializes a running total to zero and adds each element incrementally."},
    {"name": "Loop boundary with array length", "reasoning": "Index-based solutions use arr.length as the exclusive upper bound to avoid index out-of-bounds."},
    {"name": "Method return statement", "reasoning": "The method must return the computed integer, exercising the return keyword with a non-void type."}
  ]
}

=== FEW-SHOT EXAMPLE 2 ===
Problem B — Correct student solutions (n=3):

Solution 1:
```java
public static String letterGrade(int score) {
    if (score >= 90) return "A";
    else if (score >= 80) return "B";
    else if (score >= 70) return "C";
    else if (score >= 60) return "D";
    else return "F";
}
```
Solution 2:
```java
public static String letterGrade(int score) {
    String g;
    if (score >= 90) { g = "A"; }
    else if (score >= 80) { g = "B"; }
    else if (score >= 70) { g = "C"; }
    else if (score >= 60) { g = "D"; }
    else { g = "F"; }
    return g;
}
```
Solution 3:
```java
public static String letterGrade(int s) {
    if (s >= 90) return "A";
    if (s >= 80) return "B";
    if (s >= 70) return "C";
    if (s >= 60) return "D";
    return "F";
}
```
Expected JSON output:
{
  "problem_description": "Map a numeric score to a letter grade (A/B/C/D/F) using threshold-based conditionals.",
  "kcs": [
    {"name": "Multi-branch conditional chaining", "reasoning": "All solutions use if/else-if chains (or sequential ifs with early return) to partition the score into grade buckets."},
    {"name": "Numeric comparison with threshold", "reasoning": "Each branch tests the score against a fixed boundary (90, 80, 70, 60) using >= to select the grade."},
    {"name": "String return value from method", "reasoning": "The method returns a String literal, requiring correct non-void method return type declaration."},
    {"name": "Default case residual handling", "reasoning": "All solutions correctly handle scores below 60 as the final else/return without an explicit threshold check."}
  ]
}
"""

_SYSTEM_PROMPT = (
    "You are an expert CS educator specializing in introductory Java programming courses. "
    "Analyze correct student solutions to infer what Knowledge Components (KCs) are required "
    "to solve the problem. KCs must be: (a) specific and teachable (3-8 words each), "
    "(b) abstract enough to generalize across solutions, (c) 3-7 KCs per problem. "
    "Reason step-by-step: first infer what the problem asks from the code patterns, "
    "then identify the specific KCs demonstrated across the solutions."
)


def _build_kc_prompt(problem_id: int, code_samples: list[str]) -> str:
    """Construct the chain-of-thought prompt with in-context examples (Table 8)."""
    solutions = "".join(
        f"\nSolution {i}:\n```java\n{code}\n```"
        for i, code in enumerate(code_samples, 1)
    )
    return (
        f"{_FEW_SHOT_EXAMPLES}\n"
        "=== NOW ANALYZE THE FOLLOWING ===\n\n"
        f"Problem {problem_id} — Correct student solutions (n={len(code_samples)}):"
        f"{solutions}\n\n"
        "Reason step-by-step, then respond ONLY with a valid JSON object:\n"
        "{\n"
        '  "problem_description": "1-2 sentence description of what this problem requires",\n'
        '  "kcs": [\n'
        '    {"name": "KC name (3-8 words)", "reasoning": "Why this KC is needed (1 sentence)"},\n'
        "    ...\n"
        "  ]\n"
        "}"
    )


def generate_kcs_for_problem(problem_id: int, code_samples: list[str], llm: LLMClient) -> dict:
    """Generate KCs for one problem from raw Java code, via the injected LLM port.

    Raw code (not AST) is fed: Duan et al. (2025) Table 4 shows AST degrades AUC 0.812→0.784.
    Raises EmptyKCError if the problem yields 0 KCs (KC-04, defense-in-depth over the schema).
    """
    result = llm.generate(_SYSTEM_PROMPT, _build_kc_prompt(problem_id, code_samples), KC_SCHEMA)

    # ≥1 KC guard is defense-in-depth over KC_SCHEMA minItems — the job hard-fails on it (D-04).
    if not result or "kcs" not in result or not result["kcs"]:
        raise EmptyKCError(f"problema {problem_id} não gerou nenhum KC")
    return result
