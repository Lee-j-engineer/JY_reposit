// 대본(JSON) → 장면별 한국어 내레이션 MP3 + 길이 정보(manifest.json)
//
// 사용법
//   node tools/narrate.mjs --list-voices
//   node tools/narrate.mjs <대본.json> [출력폴더]
//
// 대본 형식
//   { "voiceId": "선택(없으면 ELEVENLABS_VOICE_ID)", "scenes": [ { "id": "s01_hook", "text": "..." } ] }
//
// API 키는 코드에 넣지 않습니다. SDK가 ELEVENLABS_API_KEY 환경변수를 읽습니다.
import { ElevenLabsClient } from "@elevenlabs/elevenlabs-js";
import { execFileSync } from "node:child_process";
import { mkdirSync, readFileSync, writeFileSync, existsSync } from "node:fs";
import { join } from "node:path";
import { Readable } from "node:stream";
import { createWriteStream } from "node:fs";
import { pipeline } from "node:stream/promises";

const client = new ElevenLabsClient();
const MODEL = process.env.ELEVENLABS_MODEL_ID || "eleven_multilingual_v2";

async function listVoices() {
  const res = await client.voices.search({ pageSize: 100 });
  for (const v of res.voices) {
    const l = v.labels || {};
    console.log(`${v.voiceId}\t${v.name}\t${[l.gender, l.age, l.accent, l.use_case].filter(Boolean).join(", ")}`);
  }
}

function duration(file) {
  const out = execFileSync("ffprobe", ["-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", file]);
  return Number(out.toString().trim());
}

async function narrate(scriptPath, outDir) {
  const script = JSON.parse(readFileSync(scriptPath, "utf8"));
  const voiceId = script.voiceId || process.env.ELEVENLABS_VOICE_ID;
  if (!voiceId) throw new Error("voiceId가 없습니다. 대본에 voiceId를 넣거나 ELEVENLABS_VOICE_ID를 설정하세요.");
  mkdirSync(outDir, { recursive: true });

  const manifest = { voiceId, model: MODEL, scenes: [] };
  let start = 0;
  for (const [i, scene] of script.scenes.entries()) {
    const file = join(outDir, `${scene.id}.mp3`);
    if (!existsSync(file)) { // 이미 만든 장면은 다시 생성하지 않음 (크레딧 절약)
      const audio = await client.textToSpeech.convert(voiceId, {
        text: scene.text,
        modelId: MODEL,
        languageCode: MODEL.includes("multilingual_v2") ? undefined : "ko",
        outputFormat: "mp3_44100_128",
        // 앞뒤 장면을 알려주면 장면 사이 억양이 자연스럽게 이어짐
        ...(MODEL === "eleven_v3" ? {} : { previousText: script.scenes[i - 1]?.text, nextText: script.scenes[i + 1]?.text }),
      });
      await pipeline(Readable.fromWeb(audio), createWriteStream(file));
      console.log(`생성: ${file}`);
    } else {
      console.log(`건너뜀(이미 있음): ${file}`);
    }
    const d = duration(file);
    manifest.scenes.push({ id: scene.id, text: scene.text, file, start: +start.toFixed(3), duration: +d.toFixed(3) });
    start += d;
  }
  manifest.total = +start.toFixed(3);

  // 전체 내레이션 한 파일로 합치기
  const list = join(outDir, "concat.txt");
  writeFileSync(list, manifest.scenes.map(s => `file '${s.id}.mp3'`).join("\n"));
  execFileSync("ffmpeg", ["-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", list, "-c", "copy", join(outDir, "narration_full.mp3")]);
  writeFileSync(join(outDir, "manifest.json"), JSON.stringify(manifest, null, 2));
  console.log(`완료: 장면 ${manifest.scenes.length}개, 총 ${manifest.total.toFixed(1)}초 → ${join(outDir, "manifest.json")}`);
}

const [arg, out] = process.argv.slice(2);
if (arg === "--list-voices") await listVoices();
else if (arg) await narrate(arg, out || "out/narration");
else console.log("사용법: node tools/narrate.mjs --list-voices | <대본.json> [출력폴더]");
