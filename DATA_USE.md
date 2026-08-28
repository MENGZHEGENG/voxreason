# Data Use Notes

This repository contains code, paper source, compact result inputs, and a public VoxReasonBench source-label split for listener-free speech-reasoning evaluation.

## Code License

No repository-level code license has been selected in this snapshot. Until the project owner adds one, treat the code as available for inspection and reproduction of the paper commands, but request permission before redistribution or reuse beyond that scope.

## Source-Label Data

The benchmark files under `data/benchmark/source_label/` contain derived labels, cue records, text prompts, metadata, and expected speaking plans. They do not include raw audio.

The source records come from RAVDESS: Livingstone and Russo, The Ryerson Audio-Visual Database of Emotional Speech and Song, PLOS ONE 2018; Zenodo record 1188976. The public case metadata records the source license as CC BY-NC-SA 4.0.

Users who need waveform inputs should obtain them from the original RAVDESS source and follow its license terms.

## Claim Scope

The released benchmark supports automatic process checks for evidence citation, plan-slot agreement, unsupported evidence, grounded score, and counterfactual cue consistency. It does not report listener judgments or waveform user ratings.
