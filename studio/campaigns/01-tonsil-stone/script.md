# Campaign 01 — 扁桃腺結石 (Tonsil Stone)

> TCM-Jessica marketing video. 年轻、甜美女中医师 talking avatar (粤语)。
> 流程：MiniMax 粤语配音 → 即梦 image2video / 数字人对嘴 → ffmpeg 駁片。

## Voice (CAMPAIGN DEFAULT — 已确认)
- Voice id: `Cantonese_GentleLady` (顺畅自然、唔似 AI)
- **pitch: +1** (轻轻甜啲、后生啲；切忌 +4/+6 会变 chipmunk 怪声)
- emotion: 无
- speed: 1.0
- Language: `Chinese,Yue`
- **逗号注意**：开头/句中嘅「，」会令 MiniMax 插停顿，听落似 stop。写稿尽量少用逗号，要一气呵成就拎走。

生成命令：
```bash
python3 scripts/gen_voice_clip.py --voice Cantonese_GentleLady --pitch 1 \
  --text "<稿>" --out campaigns/01-tonsil-stone/voice/clipN.mp3
```

## Clips

### Clip 1 ✅
**稿（去逗号版）：**
> 睇吓佢喉嚨入面撩咗啲咩出嚟？扁桃腺結石。佢嚟搵我嘅時候其實好尷尬，因為佢口氣一直好重，原來問題就藏喺佢喉嚨入面。

- Voice: `voice/clip1.mp3` (12.2s) ✅
- Downloads 副本: `~/Downloads/jessica-voice/clip1_tonsil-stone.mp3`
- Avatar: `avatar/` (即梦生成)
- Video: `video/` (即梦对嘴 — 12.2s 超 10s，对嘴拆 2 段)

### Clip 2–6
_(待定 — 畀稿就一次过出)_
