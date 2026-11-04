# Crew Joblist Contract

Hình dạng file `data/processed/crew-joblist-{tuần}.yaml`. `agent-crew` đọc thẳng file
này và phân rã được **không cần hỏi lại**.

## Field bắt buộc

```yaml
run_scope: "Nhóm NH=Laptop (1728 KW, 5 sub-ngành) · tuần 2026-08-24"
rank_source_date: "2026-06-11"     # cột M của Data Rank
rank_stale: true                    # true khi rank_source_date cũ hơn 14 ngày
measurement_end_date: "2026-08-18"  # E theo S1 mục 2.1, chiều page
jobs:
  - seq: 1
    title: "Khai báo Title/Desc 9 URL Laptop rank 2-5 đang giảm theo tháng"
    priority: P1
    worker_hint: antigravity
    action_family: TD               # TD | IB | IMG | AC | IL | BL | CSO | BM
    urls:
      - /laptop-asus-zenbook
      - /laptop-dell-gaming-alienware
    why: "rank Tổng 3.49 và 2.18; L1 +33,0% và +64,8% nhưng L2 −8,6% và −3,4% -> tăng ngắn hạn che xu hướng tháng giảm"
    evidence:
      - data/processed/phase04-datarank-priority-bands.txt
      - data/processed/phase02-verdict-url-level.txt
    acceptance: "2 dòng Title_Desc có cột I và J = OK sau kỳ checker daily kế tiếp"
    kpi_link: "đẩy 2 URL từ rank 2.18-3.49 lên top 1-2; chặn đà giảm L2"
```

| Field | Bắt buộc | Ghi chú |
| --- | --- | --- |
| `seq` | ✅ | số thứ tự trong run, 1-based |
| `title` | ✅ | một dòng, nói rõ làm gì cho bao nhiêu URL |
| `priority` | ✅ | `P1`–`P5` theo `action-priority-rules.md` |
| `worker_hint` | ✅ | `antigravity` / `claude` / `codex` |
| `action_family` | ✅ | `TD` / `IB` / `IMG` / `AC` / `IL` / `BL` / `CSO` / `BM` |
| `urls` | ✅ | path, không kèm host |
| `why` | ✅ | dẫn được về dòng trong `evidence` |
| `evidence` | ✅ | đường dẫn file raw/processed trong task folder |
| `acceptance` | ✅ | kiểm được bằng mắt hoặc bằng lệnh |
| `kpi_link` | ✅ | rank mục tiêu hoặc traffic mục tiêu |

Thiếu bất kỳ field nào → job không hợp lệ, `agent-crew` phải từ chối chứ không đoán bù.

## `worker_hint` theo `routing-table.md`

Phân theo **rule đã thành văn hay chưa**, không theo dễ/khó:

| Điều kiện | `worker_hint` |
| --- | --- |
| Rule đã viết trong `SKILL.md`, chỉ cần thi hành đúng và nhanh | `antigravity` |
| Cần phán đoán ngoài văn bản: đọc số, chọn hướng, quyết nghiệp vụ | `claude` |
| Code, pipeline, logic nhiều bước, refactor | `codex` |

Skill này chỉ **gợi ý**. `agent-crew` vẫn là nơi quyết cuối.

## Viết `acceptance` thế nào

Acceptance phải trỏ về **cột bằng chứng live** của S2, không phải về cảm nhận.

| Action family | Acceptance kiểm ở đâu |
| --- | --- |
| `TD` | `Title_Desc` cột I và J = `OK` |
| `IL` | `Onpage_Blog` cột F = `OK` |
| `IB` | `Infobox` cột I = `TRUE` — **kèm yêu cầu chạy `checkInfoboxArticlesAll` bằng tay**, vì tab này không có daily trigger |
| `AC` | không có checker → acceptance phải là bằng chứng người kiểm, ghi rõ ai kiểm |
| `BL` | `Content_Blog` cột L (qua `Blog_Target_Map`) — hiện `NO_CHECKER`, người điền tay |
| `CSO` | `Content_SP_Optimize` cột `Trạng thái` = `Hoàn thành` + `Product in KPI?` = `TRUE` |
| `BM` | `Backlink_Target_Map` cột `Verdict` = `OK` — checker daily 10:00, allowlist 9 host, tin được |

Cách kiểm nhanh mọi family: đọc `Action_Event!N` (`Trạng thái`) của `Data Order TGDD`,
nó mang nguyên giá trị ô bằng chứng của tab nguồn. Xem S2 mục 2.2.

"Làm cho tốt", "tối ưu content" **không phải** acceptance.

## Chia lô

`MAX_JOBS = 6` mỗi run, `MAX_PARALLEL = 3`. Quá thì:

```yaml
run_scope: "Nhóm NH=Laptop (1728 KW, 5 sub-ngành) · tuần 2026-08-24 · run 1/2"
next_run:
  contains: "P3 · 8 URL rank 5-15 CTR yếu"
  reason: "vượt MAX_JOBS 6"
```

Ghi `next_run` để người đọc biết còn gì, nhưng **không tự chạy run thứ hai**.

## Cost gate

Job cần Ahrefs, DataForSEO, Gemini API, hoặc LLM batch phải ghi:

```yaml
cost_gate: "ahrefs"
```

`agent-crew` gặp field này thì trả `BLOCKED / COST_GATE` và xin xác nhận user trước khi
dispatch.

## `run_scope` phải ghi rõ tầng phạm vi

Viết `Nhóm NH=Laptop`, không viết mỗi `Laptop`. `Laptop` một mình mơ hồ giữa
`Nhóm NH = Laptop` (1728 KW, 5 sub-ngành hàng) và `Tên Ngành hàng = laptop` (839 KW).
Worker đọc sai tầng thì làm thiếu 51% phạm vi. Xem `docs/kpi-and-owner-context.md`.
