// Build the Word report from docx-data.json (see export_docx.py). Letter, Times New Roman, template structure.
const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, WidthType, ShadingType, BorderStyle,
  AlignmentType, LevelFormat,
} = require("docx");

const [, , inPath, outPath] = process.argv;
const data = JSON.parse(fs.readFileSync(inPath, "utf8"));
const FONT = "Times New Roman";
const BODY = 22, CELL = 18; // half-points: 11pt body, 9pt table

function runs(text, size) {
  return text.split("**").map((part, i) => new TextRun({ text: part, bold: i % 2 === 1, font: FONT, size }));
}
const para = (text, opts = {}) =>
  new Paragraph({ spacing: { after: 70, line: 245 }, ...opts, children: runs(text, BODY) });

const heading = (text) =>
  new Paragraph({ spacing: { before: 140, after: 50 }, keepNext: true,
    children: [new TextRun({ text, bold: true, font: FONT, size: 24 })] });

const border = { style: BorderStyle.SINGLE, size: 4, color: "777777" };
const borders = { top: border, bottom: border, left: border, right: border };

function table(t) {
  const total = t.widths.reduce((a, b) => a + b, 0);
  const cell = (text, w, header) =>
    new TableCell({
      borders, width: { size: w, type: WidthType.DXA },
      margins: { top: 40, bottom: 40, left: 70, right: 70 },
      shading: header ? { fill: "DDDDDD", type: ShadingType.CLEAR, color: "auto" } : undefined,
      children: [new Paragraph({ spacing: { after: 0, line: 230 }, children: runs(header ? `**${text}**` : text, CELL) })],
    });
  return new Table({
    width: { size: total, type: WidthType.DXA }, columnWidths: t.widths,
    rows: [
      new TableRow({ tableHeader: true, children: t.cols.map((c, i) => cell(c, t.widths[i], true)) }),
      ...t.rows.map((r) => new TableRow({ cantSplit: true, children: r.map((c, i) => cell(c, t.widths[i], false)) })),
    ],
  });
}

const children = [];
const tm = data.team;
children.push(new Paragraph({ spacing: { after: 60 }, children: [new TextRun({ text: data.title, bold: true, font: FONT, size: 26 })] }));
children.push(para(`**Team leader:** ${tm.leader}   **Team members:** ${tm.members}   **Contact details:** ${tm.contact}   **Github link:** ${tm.github}`));

for (const s of data.sections) {
  children.push(heading(s.heading));
  if (s.table) children.push(table(s.table));
  for (const b of s.bullets || []) {
    children.push(new Paragraph({ numbering: { reference: "bullets", level: 0 }, spacing: { after: 30, line: 240 }, children: runs(b, BODY) }));
  }
  for (const p of s.paras || []) children.push(para(p));
}

const doc = new Document({
  creator: "The Human Clause team",
  title: data.title,
  styles: { default: { document: { run: { font: FONT, size: BODY } } } },
  numbering: {
    config: [{ reference: "bullets", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT,
      style: { paragraph: { indent: { left: 360, hanging: 240 } } } }] }],
  },
  sections: [{
    properties: { page: { size: { width: 12240, height: 15840 }, margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } } },
    children,
  }],
});

Packer.toBuffer(doc).then((buf) => { fs.writeFileSync(outPath, buf); });
