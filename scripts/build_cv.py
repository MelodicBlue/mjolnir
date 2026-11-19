#!/usr/bin/env python3
"""Build a one-page, ATS-safe CV PDF from a JSON spec (Jake's Resume layout, A4, xelatex).

    python3 scripts/build_cv.py applications/files/<slug>/cv.json   -> cv.pdf next to it

Spec keys: header{name, line1, line2}, sections[{title, entries[{left, right, sub, subright, bullets[]}] or lines[]}]
Every claim in the spec must come from config/answers.md.
"""
import json, os, re, subprocess, sys

ESC = {'&': r'\&', '%': r'\%', '$': r'\$', '#': r'\#', '_': r'\_', '~': r'\textasciitilde{}', '^': r'\^{}'}
def e(s):
    return ''.join(ESC.get(c, c) for c in s).replace('<b>', r'\textbf{').replace('</b>', '}')

PRE = r"""\documentclass[a4paper,11pt]{article}
\usepackage[empty]{fullpage}
\usepackage{titlesec}
\usepackage{enumitem}
\usepackage[hidelinks]{hyperref}
\usepackage{tabularx}
\usepackage{fontspec}
\setmainfont{lmroman10-regular.otf}[BoldFont=lmroman10-bold.otf, ItalicFont=lmroman10-italic.otf, Ligatures={TeX,NoCommon}]
\addtolength{\oddsidemargin}{-0.55in}\addtolength{\evensidemargin}{-0.55in}\addtolength{\textwidth}{1.1in}
\addtolength{\topmargin}{-.6in}\addtolength{\textheight}{1.2in}
\raggedright\raggedbottom\setlength{\tabcolsep}{0in}\pagestyle{empty}
\titleformat{\section}{\vspace{-5pt}\scshape\raggedright\large}{}{0em}{}[\titlerule\vspace{-5pt}]
\begin{document}
"""

def build(spec_path):
    S = json.load(open(spec_path))
    h = S['header']
    out = [PRE, r'\begin{center}{\Huge\scshape ' + e(h['name']) + r'}\\\vspace{2pt}\small ' + e(h['line1']) + r'\\\vspace{1pt}\small ' + e(h['line2']) + r'\end{center}' + '\n']
    for sec in S['sections']:
        out.append(r'\section{' + e(sec['title']) + '}\n')
        if 'lines' in sec:
            out.append(r'\begin{itemize}[leftmargin=0.1in,label={}]' + '\n')
            for l in sec['lines']: out.append(r'\small\item{' + e(l) + r'}\vspace{-3pt}' + '\n')
            out.append(r'\end{itemize}' + '\n'); continue
        out.append(r'\begin{itemize}[leftmargin=0.1in,label={}]' + '\n')
        for en in sec['entries']:
            out.append(r'\item\begin{tabular*}{0.98\textwidth}[t]{l@{\extracolsep{\fill}}r}\textbf{' + e(en['left']) + '} & ' + e(en.get('right', '')) + r' \\')
            if en.get('sub') or en.get('subright'):
                out.append(r'\textit{\small ' + e(en.get('sub', '')) + r'} & \textit{\small ' + e(en.get('subright', '')) + r'} \\')
            out.append(r'\end{tabular*}\vspace{-6pt}' + '\n')
            if en.get('bullets'):
                out.append(r'\begin{itemize}[leftmargin=0.18in,itemsep=0pt,topsep=2pt,label={\textbullet}]' + '\n')
                for b in en['bullets']: out.append(r'\item\small{' + e(b) + r'}\vspace{-2pt}' + '\n')
                out.append(r'\end{itemize}\vspace{-3pt}' + '\n')
        out.append(r'\end{itemize}' + '\n')
    out.append(r'\end{document}' + '\n')
    d = os.path.dirname(os.path.abspath(spec_path))
    tex = os.path.join(d, 'cv.tex')
    open(tex, 'w').write(''.join(out))
    r = subprocess.run(['xelatex', '-interaction=nonstopmode', '-halt-on-error', 'cv.tex'], cwd=d, capture_output=True, text=True)
    if r.returncode: sys.exit(r.stdout[-2500:])
    pages = subprocess.run(['pdfinfo', os.path.join(d, 'cv.pdf')], capture_output=True, text=True).stdout
    n = int(re.search(r'Pages:\s+(\d+)', pages).group(1))
    for ext in ('aux', 'log', 'out'):
        try: os.remove(os.path.join(d, 'cv.' + ext))
        except OSError: pass
    print(f'{d}/cv.pdf: {n} page(s)')
    if n != 1: sys.exit('CV must be exactly one page')
    if '—' in ''.join(out): sys.exit('em dash found')

if __name__ == '__main__': build(sys.argv[1])
