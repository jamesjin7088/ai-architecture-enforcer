[English](README.md) | 한국어

# ai-architecture-enforcer

Claude Code 같은 AI 코딩 에이전트가 작업하면서 프로젝트의 아키텍처를 조용히 무너뜨리지
않도록 지켜주는 플러그인입니다. 작은 설정 파일에 레이어와 규칙을 한 번 정의해두면,
플러그인이 Claude가 작업하는 동안 이를 자동으로 강제하고, 필요할 때 직접 점검할 수 있는
도구도 함께 제공합니다.

## 주요 기능

- **하드코딩이 아닌 프로젝트별 규칙.** 레이어 구조, 임포트 경계, 파일 크기 제한, 순환
  임포트 허용 여부를 프로젝트 루트의 `.architecture.json`에 직접 정의합니다. 설정 파일이
  없으면 플러그인은 아무 동작도 하지 않습니다 (기본값이 안전함).
- **요청 시뿐 아니라 실시간으로 강제.** `PostToolUse` 훅이 Claude가 수정/생성하는 모든
  파일을 규칙에 맞춰 즉시 검사하고 위반 사항을 바로 Claude에게 피드백합니다. 리뷰 단계에서
  발견하는 게 아니라 그 자리에서 스스로 고치도록 유도합니다.
- **규칙이 첫 턴부터 보임.** `SessionStart` 훅이 활성화된 규칙을 자동으로 요약해 컨텍스트에
  주입합니다.
- **필요할 때 전체 스캔/초기 설정.** 두 가지 스킬: 기존 폴더 구조를 보고 설정을 만들어주는
  `arch-init`, 전체 저장소를 스캔해 위반 사항을 모두 보여주는 `arch-check`.
- **diff 단위 심층 리뷰.** 변경 사항을 아키텍처 준수 관점에서만 집중적으로 리뷰하는
  `architecture-reviewer` 서브에이전트 (일반 코드 리뷰와는 별도 패스).

검사 항목: 파일당 최대 라인 수, 레이어 경계를 넘는 금지된 임포트, 순환 임포트 체인.
임포트 스캐너는 JS/TS(`import`, `require`)와 Python(`import`, `from ... import`) 문법을
정규식으로 인식합니다 — 완전한 컴파일러가 아니라 빠르게 동작하는 휴리스틱 린터로 의도적으로
설계했습니다.

## 설치

```
/plugin marketplace add jamesjin7088/ai-architecture-enforcer
/plugin install ai-architecture-enforcer@ai-architecture-enforcer
```

## 프로젝트에 규칙 설정하기

프로젝트 폴더에서 Claude Code 세션을 열고:

```
Run arch-init
```

폴더 구조를 살펴보고 `.architecture.json` 초안을 제안합니다 (형식은
`config/architecture.example.json` 참고). 실제로 파일을 쓰기 전에 사용자에게 확인을
요청합니다.

## 설정 파일 레퍼런스

```jsonc
{
  "maxLinesPerFile": 300,
  "excludePaths": ["node_modules", "dist", "build", ".git", "vendor"],
  "checkCircularDeps": true,
  "layers": [
    {
      "name": "domain",
      "paths": ["src/domain/**"],
      "forbiddenImports": ["src/infra/**", "src/adapters/**"]
    }
  ]
}
```

- `layers[].paths` — 이 레이어에 속하는 파일을 식별하는 glob 패턴.
- `layers[].forbiddenImports` — 이 레이어의 파일이 절대 임포트하면 안 되는 대상의 glob
  패턴. 비워두면 해당 레이어는 임포트 제한이 없습니다.
- `maxLinesPerFile` — `null`로 설정하면 파일 크기 검사를 완전히 끕니다.
- `excludePaths`는 기본 제외 목록(`node_modules`, `dist`, `build`, `.git`, `vendor`,
  `__pycache__`, `.venv`, `venv`)과 합쳐집니다.

## 수동으로 검사하기

```
Run arch-check
```

또는 직접 실행:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/cli.py" --root . --full
```

## 라이선스

MIT
