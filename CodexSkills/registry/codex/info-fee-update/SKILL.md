---
name: info-fee-update
description: Fill and update the official current-month Chinese 信息费申请表 and 2023-2025年信息费明细表 workbooks from contractor/payment notes, using Chrome 红圈 主合同 search to look up contract number and contract amount from 甲方/project keywords. Use when the user asks Codex to 信息费更新, 填信息费Excel, 开委外单/信息费单, 根据甲方去红圈查合同号/合同金额, or continue this recorded WPS/红圈 workflow.
---

# 信息费更新

## Core Rule

Operate conservatively. This workflow writes local WPS/Excel files and may read sensitive business records in Chrome 红圈. Before typing personal/contact/payment information into a live app through Computer Use, confirm if the user has not already explicitly asked to fill that exact workbook.

Do not submit approvals, click 通过/驳回, upload files, change permissions, or create/delete records in 红圈 unless the user explicitly asks and confirms at action time.

Treat the official current-month application workbook and the append-only master detail workbook as two separate mandatory deliverables. Do not report the task complete until both required destinations are written and re-opened, unless the user explicitly scopes the task to one destination.

## Required User Input

Require these fields before filling a complete row:

- 信息费对象: 姓名, 电话, 所属项目/部门, 金额, 备注/开单要求.
- 业务经理: name to put into the workbook manager field.
- 负责人/申请人: name to put into application owner/borrower-style fields when the workbook uses them.
- 甲方信息: company/customer name and, when available, project/contract keyword.
- 资金流向: cash provider and payment method when the application workbook has 支付人、支付方式 or similar fields.

If 业务经理, 负责人/申请人, or 甲方信息 is missing, stop and ask for the missing fields in a short numbered prompt. If the workbook needs 支付人 or 支付方式 and the user has not provided them, ask before assigning those fields. If only optional notes are missing, continue with blank notes.

## Known Local Files

Recorded paths:

- Monthly application workbook folder:
  `/Users/linzezhang/Downloads/信息费/信息费-2024何志琴交接版更新/信息费申请表/`
- Recorded official monthly workbook naming convention:
  `信息费申请表(修改版)2026-07.xlsx`
- Master detail workbook:
  `/Users/linzezhang/Downloads/信息费/信息费-2024何志琴交接版更新/2023-2025年信息费明细表.xls`

Recheck paths live before editing. The monthly workbook changes by month.

Monthly application workbook rule:

- Always update the official current-month workbook, based on the current date unless the user explicitly names another month. Under the recorded convention its canonical filename is `信息费申请表(修改版)YYYY-MM.xlsx`; first confirm the exact filename against nearby official monthly files.
- Treat the canonical current-month workbook as the sole monthly application deliverable. A separately created filename with a customer name, `副本`, `临时`, or another unapproved suffix does not satisfy this requirement and must not be reported as the monthly form being completed.
- If the canonical current-month workbook already exists, write the new application into that exact workbook. Preserve existing applications. When the workbook is single-contract/single-sheet in layout, duplicate its application template sheet inside the same current-month workbook, rename the new sheet with a concise contract/甲方 identifier, and populate only the new sheet. Do not overwrite an unrelated existing application's header or create a separate customer-suffixed workbook.
- If the canonical current-month workbook does not exist, copy the nearest previous official monthly application workbook to the canonical current-month filename first. Preserve all sheets, formulas, formats, print settings, merged cells, column widths, row heights, and template content exactly. Then fill only the new detail cells or a copied template sheet within that workbook.
- If there are multiple plausible canonical current-month files, or the official naming convention cannot be determined from nearby monthly files, stop and ask the user to select the designated monthly workbook. Do not invent a filename.
- Do not create a blank workbook for the monthly application form.
- For a value-only correction in an existing application sheet, change only the affected cell contents or formulas. Preserve the existing font, font size, color, borders, fills, alignment, number formats, merged cells, row heights, column widths, print settings, and sheet order exactly. Re-open and visually inspect the corrected sheet before reporting completion.

Master detail workbook rule:

- Treat `2023-2025年信息费明细表.xls` as an append-only ledger.
- Only write at the bottom/next available row.
- Never modify, delete, insert into, sort, or reformat previous historical rows unless the user explicitly asks for repair and identifies the rows.
- The master detail row `序号` and `月份` must use the target/current application month, not a copied previous row's month. For example, in July 2026 write `月份` as `2026-07` and use serials `7-1`, `7-2`, `7-3`... for that month's appended rows.
- When continuing a month, determine the next serial by scanning existing bottom/nearby rows for the same `月份`; do not blindly copy the previous row's `序号` or `月份`.
- If the immediately previous row was just created during the current run with the wrong `序号`/`月份`, it may be corrected as part of the same user-requested repair. Otherwise, preserve historical rows.

Stable `.xls` write channel:

- Do not rely on WPS coordinate clicking as the primary `.xls` writer. WPS cells may not be exposed as accessibility elements, and focus can drift.
- Do not use `xlutils/xlwt` to save this workbook directly unless a temp roundtrip has passed. This workbook contains legacy CJK date/number format records that can make `xlwt` fail or rewrite styles incorrectly.
- Preferred path for the master `.xls`: create a backup, ensure the workbook is not open in WPS, copy the bundled LibreOffice app into the task workspace if needed, patch only the copied app's `/opt/homebrew/opt/little-cms2`, `fontconfig`, and `freetype` dylib references to the bundled runtime libraries, then use an isolated LibreOffice profile to convert `.xls -> .xlsx`.
- Edit the converted `.xlsx` with the approved spreadsheet authoring runtime, copying styles from the prior row only for the newly appended row, then convert back `.xlsx -> .xls` with the patched local LibreOffice copy.
- Replace the original `.xls` only after `xlrd` re-opens the generated `.xls` and verifies the target rows/cells. If `xlrd` is unavailable, use an isolated LibreOffice re-open/temporary conversion verification path and state that fallback in the completion report. If verification fails, keep the original and report the blocker.

## Workflow

1. Parse the user's notes into rows with: name, phone, project/department, fee amount, business remarks/opening requirements, manager, owner/applicant, party A keywords, cash provider, and payment method.
2. Locate and inspect the canonical current-month 信息费申请表 workbook and the master 明细表. For the application workbook, either use the existing canonical workbook or create it under its canonical month filename according to the monthly rule. Identify the target sheet before changing cells; if a new contract needs its own sheet, duplicate the template sheet inside the canonical workbook. For the detail workbook, identify the bottom/next append row only. Do not assume the demonstration row is still empty.
3. Fill the monthly application row in the canonical workbook following the active sheet layout. The recording showed row-level fields such as 收款人 in column A, 联系方式 in column B, 职务 in column D, amount in column F, 支付人 in column G, 支付方式 in column H, 其它说明 in column I, and a concatenated helper/formula around column K, but always verify the active workbook layout first. Map the roles by business meaning: put 信息费对象 in 收款人, normalize that object's known mobile number to the workbook's existing display convention (for example `137 7121 8591`), and derive 职务 from the provided project/department and title without inventing facts; put 负责人/申请人 in the application/borrower field; put the stated cash provider in 支付人; and put the stated method in 支付方式. Use 其它说明 only for user-provided business remarks or opening requirements, such as a project issue or coordination note. Never write `付款给`, 代付, or an intermediary payment direction into 其它说明; leave it blank when no business remark is provided. Do not replace 收款人、联系方式 or 职务 with an intermediary merely because the user says cash is paid through that intermediary. For example, `魏江洪13771218591钙液分厂设备主任副厂长，余永昕现金付款给林全意` means 收款人 `魏江洪`, 联系方式 `137 7121 8591`, 职务 `设备主任、副厂长`, 支付人 `余永昕`, 支付方式 `现金`, and 其它说明留空 unless the user separately provides a business remark. Keep the helper formula aligned with the workbook's recipient/contact/job/amount convention. When a confirmed contract amount is `0`, preserve the template but make percentage/division formulas zero-safe with `IFERROR` or the workbook's equivalent blank result, then verify no target formula displays an error such as `#DIV/0!`.
4. Use 红圈 in Chrome to obtain main-contract data:
   - Open Chrome tab `cloud.hecom.cn` / 红圈.
   - Switch to the `主合同` tab.
   - Use the `搜索关键字...` search box in 主合同.
   - Search first by 甲方 keyword; refine with project/contract keywords when there are many matches.
   - Read the result row columns. Important columns from the recording: `合同名称`, `合同编号`, `甲方`, `含税合同额 (元)`, `结算金额 (元)`, and status columns.
   - The recorded example searched `双环` then `双环零星`, yielding one row with contract name `湖北双环零星维修项目施工合同（2025）`, contract number `KMX250806 -065`, party A `湖北双环科技股份有限公司`, and amount fields including `含税合同额 (元)`, `累计开票`, and `结算金额 (元)`.
   - Treat `合同编号` as the contract number. For the master detail workbook `合同金额`/I 列, 数据取值顺序 is `含税合同额 > 对应开票金额 > 结算金额`: use the first nonblank, nonzero amount in that order unless the user explicitly overrides it. `对应开票金额` means the matching invoice basis in contract detail `票税管理 -> 项目开票 -> 本次开票含税金额(元)`, matched by user notes, invoice date/month, invoice number, or amount clue. For 零星/单价/据实结算合同, when the user says to calculate by the current contract number's accumulated amount, use 按合同号下的累计开票金额: sum all `本次开票含税金额(元)` invoice rows under that contract from contract start through the 明细表 row `月份` month-end. Example: for 双环零星, a 2026-01 detail row uses the cumulative invoices from 2025-08 contract start through 2026-01; a 2026-04 detail row uses cumulative invoices through 2026-04. Do not use the main-contract list `累计开票` total for earlier row months when it includes later invoices. If several invoice rows exist and no exact or cumulative-to-month rule is available, show the candidate invoice rows and ask before writing. If all three candidate amount fields are blank or zero, report the zero/blank source data and write `0` only after explicit user confirmation. In the completion report, state which source field supplied each contract-amount group.
5. Fill one new master 明细表 row at the bottom only. Write `序号` and `月份` from the target/current month (for example `7-1` and `2026-07` for the first July 2026 row), then fill amount around column J and manager/customer/remarks across adjacent columns. Verify column headers/current row before modifying, and never change prior rows except for an explicitly requested correction of a clearly identified recent row. For a batch in the same month, assign serials sequentially in the order entered, such as `7-1`, `7-2`, `7-3`.
6. Save both workbooks. For the monthly form, save the canonical current-month filename, never only a customer-suffixed copy. Confirm saved timestamps and inspect key cells after save.

## Red Circle Search Heuristics

- Prefer exact company/甲方 name, then add project words such as `零星`, `热电`, `省煤器`, or other distinctive terms.
- If search returns multiple contracts, compare 甲方, 合同名称, 施工状态, and amount fields. Do not guess when multiple rows plausibly match; show 2-3 candidates and ask the user to choose.
- For 明细表 I 列/合同金额, do not treat zero `含税合同额` as ambiguous when a clearly matched invoice basis exists. Apply the fixed order `含税合同额 > 对应开票金额 > 结算金额`. When 红圈 only exposes a `累计开票` total in the main-contract list, open the contract detail `票税管理` tab and use `本次开票含税金额(元)` from the matching invoice row, or compute the contract-number cumulative invoice amount through the row month when the user specifies that cumulative rule. Never write the main-contract `累计开票` total into earlier historical months if it includes invoices after that row month. Ask when multiple invoice rows plausibly match, multiple contract rows plausibly match, or all candidate amount fields are blank/zero.

## Verification

Before reporting completion:

- Re-open or inspect the target cells for every inserted row.
- Re-open the canonical current-month application workbook by its exact absolute path. Verify the target sheet name, the applicant/payment/fee fields, and any zero-safe formula results. A customer-suffixed workbook alone means the monthly application step is incomplete.
- Verify the 收款人、联系方式、职务, 支付人、支付方式、其它说明, and helper formula against the parsed user input. Verify that 其它说明 contains only the user-provided business remark/opening requirement, or is blank. For a correction that changes values only, compare the affected cells' font, borders, alignment, number formats, and merged layout with the pre-edit template state, then render the corrected sheet to confirm its visual format is unchanged.
- Check no duplicate row was created from the recorded demo row.
- Report in Codex the exact canonical monthly workbook path, target sheet and cells changed, plus the master workbook, worksheet, row, and cells changed. State the values written or intentionally left blank, including the contract-amount source.
- Report any uncertain field that required user confirmation or was not written.

## Progress Report Format

At the end of meaningful runs, include: progress percentage, completed, incomplete, estimated remaining iterations/time/confidence, and recommended next step. Explicitly state the monthly application status as `已写入正式月份申请表` or `未写入正式月份申请表`, with the canonical file path or blocker.
