# Memory Feasibility Report

**Decision:** NO-GO

**Reason:** VibeVoice-ASR failed to load: The checkpoint you are trying to load has model type `vibevoice` but Transformers does not recognize this architecture. This could be because of an issue with the checkpoint, or because your version of Transformers is out of date.

You can update Transformers with the command `pip install --upgrade transformers`. If this does not work, and the checkpoint is very new, then there may not be a release version that supports this model yet. In this case, you can get the most up-to-date code by installing Transformers from source with the command `pip install git+https://github.com/huggingface/transformers.git`

**Action:** Use SenseVoice fallback in Task 4
