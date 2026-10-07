const express = require('express');
const PDFDocument = require('pdfkit');

const app = express();
app.use(express.json({ limit: '5mb' }));

const COR = {
  primaria: '#0F766E',   // teal
  primariaClara: '#CCFBF1',
  escura: '#0F172A',
  cinza: '#64748B',
  linha: '#E2E8F0',
  fundo: '#F8FAFC',
  barra: '#14B8A6',
  branco: '#FFFFFF',
};

const brl = (v) =>
  'R$ ' + Number(v || 0).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

const periodoLabel = (p) =>
  ({ hoje: 'Hoje', semana: 'Últimos 7 dias', mes: 'Este mês' }[p] || 'Período');

function gerarPDF(dados, stream) {
  const doc = new PDFDocument({ size: 'A4', margin: 0, bufferPages: true });
  doc.pipe(stream);

  const M = 48;                 // margem
  const LARGURA = doc.page.width;
  const CONTEUDO = LARGURA - M * 2;

  // ---- Cabeçalho ----
  doc.rect(0, 0, LARGURA, 120).fill(COR.primaria);
  doc.fillColor(COR.branco).fontSize(22).font('Helvetica-Bold')
    .text('Relatório Financeiro', M, 38);
  doc.fontSize(11).font('Helvetica')
    .text(`${periodoLabel(dados.periodo)}  •  Gerado em ${dados.gerado_em || ''}`, M, 70);
  doc.fontSize(9).fillColor(COR.primariaClara)
    .text('Agente Financeiro via WhatsApp', M, 90);

  // ---- Card de total ----
  let y = 150;
  doc.roundedRect(M, y, CONTEUDO, 74, 10).fill(COR.fundo);
  doc.fillColor(COR.cinza).fontSize(10).font('Helvetica').text('TOTAL GASTO', M + 20, y + 16);
  doc.fillColor(COR.primaria).fontSize(26).font('Helvetica-Bold').text(brl(dados.total), M + 20, y + 30);
  const qtd = (dados.linhas || []).length;
  doc.fillColor(COR.cinza).fontSize(10).font('Helvetica')
    .text(`${qtd} lançamento${qtd === 1 ? '' : 's'}`, M + 20, y + 52, { width: CONTEUDO - 40, align: 'right' });
  y += 100;

  // ---- Gastos por categoria (barras) ----
  const cats = dados.por_categoria || [];
  if (cats.length) {
    doc.fillColor(COR.escura).fontSize(14).font('Helvetica-Bold').text('Gastos por categoria', M, y);
    y += 26;
    const maxCat = Math.max(...cats.map((c) => Number(c.total) || 0), 1);
    for (const c of cats) {
      const total = Number(c.total) || 0;
      const pct = dados.total ? (total / dados.total) * 100 : 0;
      doc.fillColor(COR.escura).fontSize(10).font('Helvetica-Bold').text(c.categoria, M, y, { width: 140, continued: false });
      doc.fillColor(COR.cinza).font('Helvetica').text(`${pct.toFixed(0)}%`, M + 145, y, { width: 40, align: 'right' });
      const barraX = M + 195;
      const barraW = CONTEUDO - 195 - 90;
      doc.roundedRect(barraX, y + 2, barraW, 10, 5).fill(COR.linha);
      doc.roundedRect(barraX, y + 2, Math.max(6, (total / maxCat) * barraW), 10, 5).fill(COR.barra);
      doc.fillColor(COR.escura).font('Helvetica-Bold').text(brl(total), LARGURA - M - 90, y, { width: 90, align: 'right' });
      y += 24;
    }
    y += 12;
  }

  // ---- Detalhamento (tabela) ----
  doc.fillColor(COR.escura).fontSize(14).font('Helvetica-Bold').text('Detalhamento', M, y);
  y += 24;

  const colX = [M, M + 80, M + 250, LARGURA - M - 90];
  const colW = [80, 170, LARGURA - M - 90 - (M + 250), 90];

  function cabecalhoTabela() {
    doc.rect(M, y, CONTEUDO, 22).fill(COR.primaria);
    doc.fillColor(COR.branco).fontSize(9).font('Helvetica-Bold');
    doc.text('DATA', colX[0] + 6, y + 7, { width: colW[0] });
    doc.text('DESCRIÇÃO', colX[1] + 6, y + 7, { width: colW[1] });
    doc.text('CATEGORIA', colX[2] + 6, y + 7, { width: colW[2] });
    doc.text('VALOR', colX[3], y + 7, { width: colW[3], align: 'right' });
    y += 22;
  }

  cabecalhoTabela();
  let i = 0;
  for (const l of dados.linhas || []) {
    if (y > doc.page.height - 90) {
      doc.addPage();
      y = 60;
      cabecalhoTabela();
    }
    if (i % 2 === 0) doc.rect(M, y, CONTEUDO, 20).fill(COR.fundo);
    doc.fillColor(COR.escura).fontSize(9).font('Helvetica');
    doc.text(String(l.data || ''), colX[0] + 6, y + 6, { width: colW[0] });
    doc.text(String(l.descricao || '').slice(0, 42), colX[1] + 6, y + 6, { width: colW[1] - 6 });
    doc.text(String(l.categoria || 'Outros'), colX[2] + 6, y + 6, { width: colW[2] - 6 });
    doc.font('Helvetica-Bold').fillColor(COR.primaria)
      .text(brl(l.valor), colX[3], y + 6, { width: colW[3], align: 'right' });
    y += 20;
    i++;
  }

  if (!(dados.linhas || []).length) {
    doc.fillColor(COR.cinza).fontSize(11).font('Helvetica')
      .text('Nenhum gasto registrado neste período.', M, y + 10);
  }

  // ---- Rodapé com número de páginas ----
  const range = doc.bufferedPageRange();
  for (let p = range.start; p < range.start + range.count; p++) {
    doc.switchToPage(p);
    const base = doc.page.height - 36;
    doc.fillColor(COR.cinza).fontSize(8).font('Helvetica')
      .text('Gerado pelo Agente Financeiro • WhatsApp', M, base, { width: CONTEUDO / 2 });
    doc.text(`Página ${p + 1} de ${range.count}`, M, base, { width: CONTEUDO, align: 'right' });
  }

  doc.end();
}

app.get('/health', (_req, res) => res.json({ status: 'ok' }));

app.post('/pdf', (req, res) => {
  try {
    const dados = req.body || {};
    res.setHeader('Content-Type', 'application/pdf');
    res.setHeader('Content-Disposition', 'inline; filename="relatorio-financeiro.pdf"');
    gerarPDF(dados, res);
  } catch (err) {
    console.error('Erro ao gerar PDF:', err);
    res.status(500).json({ error: err.message });
  }
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`financas-pdf rodando na porta ${PORT}`));
