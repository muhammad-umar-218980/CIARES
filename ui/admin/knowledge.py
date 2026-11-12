"""Admin knowledge-base explorer: every rule, condition and source."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from knowledge_base.knowledge_acquisition import validate_catalogue
from knowledge_base.rule_registry import ALL_RULES, MODULES, RULES_BY_MODULE
from ui.shared.layout import metric_row

EXPLANATION = (
    "A condition is one declarative triple (field, operator, value). Conditions are "
    "data, not code, which is why they can be counted, validated and printed. A rule "
    "fires only when every one of its conditions is satisfied; a condition that "
    "references an Unknown fact cannot be satisfied."
)


def render() -> None:
    report = validate_catalogue(ALL_RULES)

    metric_row(
        [
            ("Rules", len(ALL_RULES), "Manually authored IF-THEN rules"),
            ("Logical conditions", report.condition_count, "Assignment minimum is 50"),
            (
                "Distinct fact fields",
                report.distinct_condition_fields,
                "Unique facts referenced by conditions",
            ),
            ("Modules", len(MODULES), "Specialised cybersecurity areas"),
        ]
    )

    if report.errors:
        st.error(
            "Knowledge base validation failed:\n\n"
            + "\n".join(f"- {error}" for error in report.errors)
        )
    else:
        st.success(
            "Knowledge base structure is valid: unique IDs, conditions present, "
            "severities and sources approved."
        )
    st.caption(EXPLANATION)

    tabs = st.tabs([f"{module} ({len(RULES_BY_MODULE[module])})" for module in MODULES])
    for tab, module in zip(tabs, MODULES):
        rules = RULES_BY_MODULE[module]
        with tab:
            if not rules:
                st.info("No rules are registered in this module.")
                continue
            st.dataframe(
                pd.DataFrame(
                    [
                        {
                            "Rule": rule.id,
                            "Name": rule.name,
                            "Conditions": rule.condition_count,
                            "Conclusion": rule.conclusion_label,
                            "Severity": rule.severity.value,
                            "Response": rule.recommended_action or "—",
                            "Source": rule.source,
                        }
                        for rule in rules
                    ]
                ),
                hide_index=True,
            )
            for rule in rules:
                with st.expander(f"{rule.id} · {rule.name}"):
                    st.write(rule.description)
                    st.dataframe(
                        pd.DataFrame(
                            [
                                {
                                    "Condition": condition.describe(),
                                    "Field": condition.field,
                                    "Operator": condition.operator,
                                    "Value": str(condition.value),
                                }
                                for condition in rule.conditions
                            ]
                        ),
                        hide_index=True,
                    )
                    st.markdown(
                        f"**IF** {rule.describe_conditions()}  \n"
                        f"**THEN** `{rule.conclusion_key}` = True "
                        f"({rule.conclusion_label})  \n"
                        f"**Severity** {rule.severity.value} · **Source** {rule.source}"
                    )

    st.divider()
    st.markdown("#### Condition inventory")
    st.caption(
        "Machine-generated from the rule objects; this is the evidence for the "
        "50-condition requirement."
    )
    st.dataframe(
        pd.DataFrame(report.inventory).rename(
            columns={
                "field": "Fact field",
                "conditions": "Conditions",
                "rules": "Rules using it",
            }
        ),
        hide_index=True,
    )
