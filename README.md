# Projeto
Este projeto investiga uma questão central da educação pública brasileira: 
**a infraestrutura de uma escola influencia o desempenho dos seus alunos?**

Santa Maria é o maior município do interior gaúcho e concentra uma rede escolar diversa com escolas federais, estaduais e privadas, o que torna o recorte municipal ideal para comparar realidades muito distintas dentro de um mesmo território.

---

## 🗂️ Fontes de Dados

| Fonte | Descrição |
|---|---|
| **Censo Escolar 2025 (INEP)** | Dados de infraestrutura física de todas as escolas do município |
| **Microdados do ENEM** | Notas individuais dos alunos por escola, filtradas para Santa Maria/RS |

---

## ⚙️ Metodologia

## 0. Criação da database
Para iniciarmos as consultas, criei uma database (.db) pelo próprio SQLite no Visual Studio Code.

Primeiro, tive que iniciá-lo utilizando 

```sql
sqlite3 censo_escolar.db -- inicia a database que vamos utilizar
.mode csv -- entende que iremos ler CSVs, modo que o Governo disponibiliza os dados
.separator ";" -- entende que iremos separar as colunas com ";", modo que o Governo separa os dados CSVs

-- importação das tabelas para a database
.import "/.../dados/Tabela_Matricula_2025.csv" matricula 
.import "/.../dados/Tabela_Turma_2025.csv" turma
.import "/.../dados/Tabela_Escola_2025.csv" escola
.import "/.../dados/Tabela_Docente_2025.csv" docente
.import "/.../dados/Tabela_Gestor_Escolar_2025.csv" gestor_escolar
.import "/.../dados/Tabela_Curso_Tecnico_2025.csv" curso_tecnico
.import "/.../dados/RESULTADOS_ENEM.csv" resultados
```

Curiosidade: A database ficou gigante! São 2,2 GB de arquivo de dados, mas filtrando por Santa Maria, onde faremos, fica mais tranquilo. 😅

## 1. Consultas iniciais

A partir dessa primeira consulta, poderemos ter um norte de como seguiremos com o projeto. Com ela, saberemos a quantidade total de escolas que iremos trabalhar.

```sql
SELECT *
FROM escola
WHERE NO_MUNICIPIO = 'Santa Maria' AND SG_UF = 'RS';
```

Depois disso, foi necessário reunir todas as tabelas que os dados do Ministério da Educação proporcionou, para podermos relacionar e, logo depois, realizar as manipulações e extrações de dados necessárias.

```sql
SELECT * FROM escola AS e1

LEFT JOIN turma AS e2 
ON e1.CO_ENTIDADE = e2.CO_ENTIDADE

LEFT JOIN gestor_escolar AS e3
ON e1.CO_ENTIDADE = e3.CO_ENTIDADE

LEFT JOIN matricula AS e4
ON e1.CO_ENTIDADE = e4.CO_ENTIDADE

LEFT JOIN docente AS e5
ON e1.CO_ENTIDADE = e5.CO_ENTIDADE

WHERE e1.NO_MUNICIPIO = 'Santa Maria' 
      AND e1.SG_UF = 'RS'
```


### 1. Índice de Infraestrutura Escolar (IIE)

A partir das variáveis do Censo Escolar, foi construído um índice composto que avalia cada escola em quatro dimensões, com pesos proporcionais ao impacto pedagógico:

| Dimensão | Indicadores | Peso |
|---|---|---|
| Saneamento básico | Água potável, energia elétrica, esgoto, coleta de lixo, banheiro, cozinha | 1 por item |
| Espaços pedagógicos | Biblioteca, laboratório de ciências, laboratório de informática, quadra esportiva, sala de professores, refeitório, pátio coberto | 2 por item |
| Tecnologia | Internet, banda larga, computadores, equipamento multimídia | 2 por item |
| Acessibilidade & extras | Rampas, corrimão, piso tátil, auditório, banheiro PNE | 1 por item (penalidade se nenhum recurso) |

A pontuação bruta (máximo de 36 pontos) foi normalizado para uma escala de **0 a 100**, para ficar mais prático. Ou seja, 36 pontos = 100%. 
As escolas foram classificadas em três categorias:

| Categoria | Pontuação | Escolas |
|---|---|---|
| 🟢 Boa | ≥ 75 pontos | 67 escolas (34%) |
| 🟡 Mediana | 61 – 74 pontos | 67 escolas (34%) |
| 🔴 Precária | < 61 pontos | 61 escolas (31%) |

### 2. Médias do ENEM por Escola

A partir dos microdados do ENEM, as notas individuais foram agregadas por escola (`CO_ESCOLA`), calculando a média de cada área separadamente e a média geral, podendo evitar o problema de registros com notas ausentes (`NULL`) que descartariam alunos indevidamente se somados antes de agregar.

```sql
SELECT
    CO_ESCOLA,
    COUNT(*)                       AS QT_ALUNOS,
    ROUND(AVG(NU_NOTA_CN), 1)      AS MEDIA_CN,
    ROUND(AVG(NU_NOTA_CH), 1)      AS MEDIA_CH,
    ROUND(AVG(NU_NOTA_LC), 1)      AS MEDIA_LC,
    ROUND(AVG(NU_NOTA_MT), 1)      AS MEDIA_MT,
    ROUND(AVG(NU_NOTA_REDACAO), 1) AS MEDIA_RED,
    ROUND(
        (AVG(NU_NOTA_CN) + AVG(NU_NOTA_CH) + AVG(NU_NOTA_LC) + AVG(NU_NOTA_MT) + AVG(NU_NOTA_REDACAO)) / 5.0
    , 1)                           AS MEDIA_GERAL
FROM resultados
WHERE SG_UF_ESC = 'RS'
GROUP BY CO_ESCOLA
ORDER BY MEDIA_GERAL DESC;
```

### 3. Cruzamento e Análise

O vínculo entre as duas bases é feito pelo código da escola (`CO_ENTIDADE` no Censo = `CO_ESCOLA` no ENEM). Em termos "SQL", poderia ser chamado de `ID ou chaves primárias`, utilizadas para vincular duas ou mais tabelas pelo `JOIN`.

A análise vai combinar:
- **Correlação** entre IIE e média geral do ENEM
- **Comparação por categoria** de infraestrutura (Boa/Mediana/Precária)
- **Comparação por dependência administrativa** (Federal/Estadual/Privada)
- **Casos de destaque**: escolas com infraestrutura precária e bom desempenho, ou o inverso

---

## 📊 Resultados Esperados

Com base na análise, esperamos responder a perguntas como:
- Existe correlação entre infraestrutura e nota no ENEM em Santa Maria?
- As escolas estaduais, que concentram a maioria das classificadas como precárias, apresentam as menores médias?
- Quais escolas surpreendem — para cima ou para baixo — em relação ao que sua infraestrutura sugeriria?
- A infraestrutura tecnológica (internet, computadores) tem correlação mais forte com o desempenho do que o saneamento básico?

Os resultados podem contribuir para **decisões de investimento em infraestrutura escolar**, apontando onde a melhoria física teria maior potencial de impacto no aprendizado.

---

## 🗺️ Panorama Inicial (Censo Escolar 2025)

Das **195 escolas** analisadas em Santa Maria:

- Escolas **privadas** dominam o topo do índice de infraestrutura
- Escolas **estaduais** concentram 39 das 61 classificadas como precárias
- Escolas **federais** (UFSM/Politécnico e Colégio Militar) pontuam no máximo do índice
- **31%** das escolas do município operam com infraestrutura precária

---

## 📁 Estrutura do Repositório

```
.
├── data/
│   ├── Colegios_santa_maria.csv      # Censo Escolar 2025 — infraestrutura
│   └── Notas_santa_maria.csv         # Microdados ENEM — notas por aluno
├── outputs/
│   ├── infra_scores.csv              # IIE calculado por escola
├── analysis/
    └── (dashboards em desenvolvimento)
```

---

## 🚧 Status do Projeto

- [x] Coleta e limpeza dos dados do Censo Escolar
- [x] Construção do Índice de Infraestrutura Escolar (IIE)
- [x] Classificação das 195 escolas em Boa / Mediana / Precária
- [x] Dashboard interativo de infraestrutura
- [x] Coleta e validação dos microdados do ENEM
- [x] Cruzamento IIE × médias do ENEM
- [ ] Análise de correlação e visualizações finais
- [ ] Relatório de conclusões

---

## 🛠️ Tecnologias

- **Python** (pandas) — processamento e análise dos dados
- **SQL (SQLite)** — agregação dos microdados do ENEM
- **Power BI** — ferramenta utilizada para a criação dos dashboards, visualização e análise dos dados
- **VS Code** — IDE utilizada

---

## 📜 Fonte

Dados públicos provenientes do INEP e Ministério da Educação.
