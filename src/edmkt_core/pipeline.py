"""edmkt_core public pipeline glue (DataFrame in / artifacts out).

Intentionally empty for now. Created in plan 01 so later plans MODIFY rather than
CREATE this module, but it carries no logic yet — the public glue is a TDD feature.

# TODO(plan 04): split_by_subject(df, test_size=0.2, random_state=1, min_attempts=3)
#                — extract split logic from data_loader.load_spring2019_split (Pitfall 3:
#                random_state=1, NOT 42); also accept pre-split partitions.
# TODO(plan 05): train_and_evaluate public glue — preserve operation order (Pitfall 2):
#                build_sequences → split → build_cache → build_vocab(train-only, CORE-04)
#                → build_problem_index(all) → truncate_sequences(slice-only, CORE-05)
#                → train_and_evaluate → {model, vocab, config, first_auc, all_auc, pred_df}.
"""
