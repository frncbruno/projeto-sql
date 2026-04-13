# Projeto
Este projeto investiga uma questão central da educação pública brasileira: 
**a infraestrutura de uma escola influencia o desempenho dos seus alunos?**

Santa Maria é o maior município do interior gaúcho e concentra uma rede escolar diversa com escolas federais, estaduais e privadas, o que torna o recorte municipal ideal para comparar realidades muito distintas dentro de um mesmo território.

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

## 2. Limpeza e tratamento dos dados (Data Cleaning)

Antes de calcular o IIE e cruzar com o ENEM, foram realizadas as seguintes etapas de limpeza e tratamento sobre os dados brutos:

**Censo Escolar:**
- Filtragem por município (`NO_MUNICIPIO = 'Santa Maria'`) e estado (`SG_UF = 'RS'`), reduzindo de ~180 mil escolas nacionais para 195 escolas locais
- Seleção das colunas relevantes para o IIE (indicadores `IN_*`) e identificação (`CO_ENTIDADE`, `NO_ENTIDADE`, `TP_DEPENDENCIA`)
- Tratamento de valores nulos (registros com `NULL` nos indicadores de infraestrutura foram tratados como ausência do recurso (`0`))

**Microdados do ENEM:**
- Filtragem por `SG_UF_ESC = 'RS'` para manter apenas alunos de escolas gaúchas
- Remoção de registros com todas as cinco notas nulas (alunos ausentes ou que não realizaram o exame)
- Agregação por escola (`CO_ESCOLA`): as médias de cada área foram calculadas com `AVG()` por coluna separadamente, ignorando `NULL`

**Cruzamento:**
- Join entre as duas bases via `CO_ENTIDADE` (Censo) = `CO_ESCOLA` (ENEM)
- Das 195 escolas do Censo, 38 possuíam correspondência nos microdados do ENEM — as demais são creches e escolas de ensino fundamental, que não participam do exame

**Power BI:**
- Foram tratadas as colunas necessárias via Power Query, identificando-as como percentual, decimal, número inteiro ou texto
- Também no BI, foram unidas pela cardinalidade 1:1, por join `CO_ENTIDADE` (Censo) = `CO_ESCOLA` (ENEM)


### 3. Índice de Infraestrutura Escolar (IIE)

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

### 4. Médias do ENEM por Escola

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

### 5. Cruzamento e Análise

O vínculo entre as duas bases é feito pelo código da escola (`CO_ENTIDADE` no Censo = `CO_ESCOLA` no ENEM). Em termos "SQL", poderia ser chamado de `ID ou chaves primárias`, utilizadas para vincular duas ou mais tabelas pelo `JOIN`.

A análise vai combinar:
- **Correlação** entre IIE e média geral do ENEM
- **Comparação por categoria** de infraestrutura (Boa/Mediana/Precária)
- **Comparação por tipo de escola na questão administrativa** (Federal/Estadual/Privada)
- **Casos de destaque**: escolas com infraestrutura precária e bom desempenho, ou o inverso

---

## 📊 Resultados

Das **38 escolas** com dados completos de infraestrutura e ENEM:

### Média ENEM por categoria de infraestrutura

| Categoria | IIE médio | Média ENEM | Alunos |
|---|---|---|---|
| 🟢 Boa | 86,3 | 573,2 | 1.442 |
| 🟡 Mediana | 67,5 | 555,3 | 233 |
| 🔴 Precária | 52,8 | 504,8 | 251 |

### Média ENEM por tipo de escola

| Tipo | IIE médio | Média ENEM |
|---|---|---|
| Federal | 93,5 | 678,2 |
| Privada | 84,9 | 622,4 |
| Estadual | 73,6 | 506,3 |

### Distribuição de infraestrutura por tipo de escola
- **100%** das escolas federais possuem infraestrutura classificada como Boa
- **85,7%** das privadas possuem infraestrutura Boa
- As escolas estaduais são as mais divergentes: 57,1% Boa, 23,8% Mediana e 19,1% Precária

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
│   ├── raw/                              # Dados originais (raw)
│   │   ├── Colegios_santa_maria_raw.csv  # Censo Escolar 2025 — infraestrutura
│   │   └── Notas_santa_maria_raw.csv     # Microdados ENEM — notas por aluno
│   └── censo_escolar.db                  # Database SQLite
├── outputs/
│   ├── infra_pontuacao.csv               # IIE calculado por escola
│   ├── dim_escolas.csv                   # Tabela dimensional para Power BI
│   └── fato_enem.csv                     # Tabela de médias ENEM por escola para Power BI
├── analysis/
│   ├── calculo_iie.py                    # Cálculo do Índice de Infraestrutura
│   ├── medias_enem.py                    # Agregação das notas por escola
│   └── cruzamento.py                     # Cruzamento IIE × ENEM e correlação
├── dashboard_powerbi/                    # Dashboards em Power BI (.pbix)
├── requirements.txt                      # Dependências Python
└── README.md
```

---

## 📸 Dashboard

  <img width="1278" height="717" alt="Pagina1" src="https://github.com/user-attachments/assets/76cafaa5-904d-40ea-b35a-8f948690f9fc" />
  
  <img width="1273" height="709" alt="Pagina2" src="https://github.com/user-attachments/assets/cae6b16f-d8b9-4b85-8fa9-3f5c5a28db37" />

---

## 💡 Conclusões

- 68 pontos separam escolas Boas das Precárias. A diferença na média geral do ENEM entre as duas categorias pode soar um grande alarme.
- Nem toda infraestrutura impacta da mesma forma. Saneamento e tecnologia, isoladamente, não apresentaram correlação significativa com o ENEM. Espaços pedagógicos e acessibilidade sim, o que muda a conversa sobre onde investir primeiro.
- Escolas federais lideram em tudo. Com 100% de infraestrutura Boa e média ENEM de 678,2, as federais ficam bem acima das outras, reflexo de maior aporte de recursos e, em parte, de maior seletividade no acesso.
- As estaduais são o grupo mais desigual. Com espectro que vai de infraestrutura plena a precária e média ENEM de 506,3, as escolas estaduais concentram a maior desigualdade e o maior potencial de ganho com investimentos estruturais.
- Há exceções relevantes nos dois sentidos. O Instituto Olavo Bilac (IIE 52,8 → 526 pts) performa acima do esperado para sua infraestrutura, sugerindo gestão ou corpo docente diferenciados. Diferentemente de ET Albert Einstein (IIE 77,8 → 479 pts), ficando abaixo do padrão das privadas com infraestrutura equivalente. Esses casos mostram que infraestrutura importa, mas não explica tudo. Fatores como qualidade docente, gestão escolar e contexto socioeconômico dos alunos não estão capturados nesta análise e merecem investigação para ser mais assertivo.
- 31% das escolas municipais operam em condições precárias. Embora não participem do ENEM, esse dado aponta uma desigualdade estrutural relevante que afeta a base da educação no município.

---

## 🎯 Recomendações

Com base nos achados, algumas direções concretas para gestores da rede pública de Santa Maria:

- Priorizar espaços pedagógicos nas escolas estaduais precárias. Das 9 escolas estaduais com infraestrutura Precária, nenhuma possui pátio coberto, apenas 11% têm quadra de esportes e 22% têm laboratório de ciências, exatamente os recursos com maior correlação com o desempenho no ENEM. Intervenções nesses espaços têm maior respaldo nos dados do que, por exemplo, ampliar conectividade isoladamente.
- Investigar as escolas que performam acima do esperado. O Instituto Olavo Bilac entrega resultados acima da média com infraestrutura precária. Entender o que essas escolas fazem de diferente (gestão, metodologia, perfil docente) pode gerar aprendizados replicáveis para toda a rede estadual, sem depender de obras.
- Não tratar tecnologia como solução isolada. A a relação entre a dimensão de tecnologia e o ENEM não foi estatisticamente significativa nesta amostra. Isso não significa que tecnologia não importa, mas sugere que investimentos em conectividade sem acompanhamento pedagógico estruturado podem ter retorno limitado.
- Os espaços pedagógicos (bibliotecas, laboratórios, quadras) e a acessibilidade são as dimensões com maior associação estatística com os resultados. Isso sugere que, do ponto de vista de priorização de investimentos, obras e equipamentos diretamente ligados ao ambiente de aprendizagem têm maior retorno mensurável do que conectividade ou infraestrutura básica isoladas.

> ⚠️ **Limitação importante:** Fatores como nível socioeconômico dos alunos, qualidade docente e gestão escolar não foram controlados e podem explicar parte ou toda a relação observada. As recomendações acima devem ser tratadas como hipóteses a investigar, não como conclusões definitivas.

---

## 🚧 Status do Projeto

- [x] Coleta e limpeza dos dados do Censo Escolar
- [x] Construção do Índice de Infraestrutura Escolar (IIE)
- [x] Classificação das 195 escolas em Boa / Mediana / Precária
- [x] Coleta e validação dos microdados do ENEM
- [x] Cruzamento IIE × médias do ENEM
- [x] Dashboard interativo no Power BI (2 páginas)
- [x] Relatório de conclusões

---

## 🛠️ Tecnologias

- **Python 3.12.3** — linguagem principal
  - `pandas 3.0.1` — processamento e análise dos dados
- **SQL (SQLite)** — agregação dos microdados do ENEM
- **Power BI** — criação dos dashboards, visualização e análise dos dados
- **VS Code** — IDE utilizada

---

## 📜 Fonte

Dados públicos provenientes do INEP e Ministério da Educação.
- [Censo Escolar 2025](https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados/censo-escolar)
- [Microdados ENEM](https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados)
