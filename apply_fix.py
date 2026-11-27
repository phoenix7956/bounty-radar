# -*- coding: utf-8 -*-
"""Expensify/App #106035 - apply the verified fix in place (CRLF-safe)."""
import os
import sys

BASE = r"C:\Users\mm155\expensify106035\App"

EDITS = [
    (r"src\pages\inbox\report\useDebouncedSaveDraft.ts", [
        ("import useDebounce from '@hooks/useDebounce';",
         "import {useDebounceWithControls} from '@hooks/useDebounce';"),
        ("    const debouncedSaveDraft = useDebounce(",
         "    const {invoke: debouncedSaveDraft, cancel: cancelDebouncedSaveDraft} = useDebounceWithControls("),
        ("    const cancelSaveDraft = () => {\n"
         "        isSavePending.current = false;\n"
         "    };",
         "    const cancelSaveDraft = () => {\n"
         "        isSavePending.current = false;\n"
         "        cancelDebouncedSaveDraft();\n"
         "    };"),
    ]),
    (r"src\pages\inbox\report\ReportActionCompose\ComposerWithSuggestions.tsx", [
        ("    const {saveDraft: debouncedSaveComment, isSavePending: isCommentSavePending} = useDebouncedSaveDraft(",
         "    const {saveDraft: debouncedSaveComment, isSavePending: isCommentSavePending, cancelSaveDraft: cancelSaveComment} = useDebouncedSaveDraft("),
        ("        if (shouldDebounceSaveComment) {\n"
         "            debouncedSaveComment(newCommentConverted);\n"
         "        } else {\n"
         "            saveReportDraftComment(reportID, newCommentConverted);\n"
         "        }",
         "        // Clearing the composer has to be persisted synchronously: the debounced save would not run before the\n"
         "        // page tears down, leaving the stale draft in storage and resurrecting it the next time the report opens.\n"
         "        // Cancelling the pending debounced save also stops a queued non-empty save from overwriting the cleared draft.\n"
         "        if (!newCommentConverted) {\n"
         "            cancelSaveComment();\n"
         "            saveReportDraftComment(reportID, '');\n"
         "        } else if (shouldDebounceSaveComment) {\n"
         "            debouncedSaveComment(newCommentConverted);\n"
         "        } else {\n"
         "            saveReportDraftComment(reportID, newCommentConverted);\n"
         "        }"),
    ]),
]


def main():
    for rel, reps in EDITS:
        path = os.path.join(BASE, rel)
        if not os.path.exists(path):
            print("MISSING FILE:", path)
            return 1
        with open(path, "r", encoding="utf-8", newline="") as fh:
            raw = fh.read()
        crlf = "\r\n" in raw
        text = raw.replace("\r\n", "\n")
        for old, new in reps:
            if old not in text:
                print("NO MATCH in %s:\n%s" % (rel, old[:120]))
                return 1
            text = text.replace(old, new, 1)
        out = text.replace("\n", "\r\n") if crlf else text
        with open(path, "w", encoding="utf-8", newline="") as fh:
            fh.write(out)
        print("PATCHED:", rel, "(crlf=%s)" % crlf)
    return 0


if __name__ == "__main__":
    sys.exit(main())
