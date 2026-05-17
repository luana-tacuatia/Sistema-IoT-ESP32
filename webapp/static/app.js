let chart
let periodoAtual = '30min'

const PERIODOS = {
  '30min': { modoTimestamp: 'hora' },
  '1h': { modoTimestamp: 'hora' },
  '24h': { modoTimestamp: 'hora' },
  '1mes': { modoTimestamp: 'dia' },
  '6m': { modoTimestamp: 'mes' },
  '12m': { modoTimestamp: 'mes' },
}

// ── Disponibilidade dos botões ──────────────────────────────────────────────

async function atualizarBotoesDisponiveis() {
  let disponibilidade
  try {
    const response = await fetch('/api/periodos-disponiveis')
    if (!response.ok) throw new Error(`Erro HTTP: ${response.status}`)
    disponibilidade = await response.json()
  } catch (err) {
    console.error('Erro ao verificar períodos disponíveis:', err)
    return
  }

  document.querySelectorAll('[data-periodo]').forEach((btn) => {
    const periodo = btn.dataset.periodo
    const disponivel = disponibilidade[periodo] ?? false

    btn.disabled = !disponivel
    btn.title = disponivel
      ? ''
      : 'Ainda não há dados suficientes para este período'

    // Se o período ativo ficou desabilitado, migra para o primeiro disponível
    if (!disponivel && periodo === periodoAtual) {
      const primeiro = Object.keys(disponibilidade).find(
        (p) => disponibilidade[p],
      )
      if (primeiro) carregarDados(primeiro)
    }
  })
}

// ── Carregamento de dados e gráfico ────────────────────────────────────────

async function carregarDados(periodo = '30min') {
  periodoAtual = periodo

  const mensagem = document.getElementById('mensagemSemDados')
  const containerGrafico = document.getElementById('containerGrafico')

  document.querySelectorAll('[data-periodo]').forEach((btn) => {
    btn.classList.toggle('ativo', btn.dataset.periodo === periodo)
  })

  mensagem.style.display = 'block'
  mensagem.textContent = 'Carregando dados...'
  containerGrafico.style.display = 'none'

  let dados
  try {
    const response = await fetch(`/api/dados?periodo=${periodo}`)
    if (!response.ok) throw new Error(`Erro HTTP: ${response.status}`)
    dados = await response.json()
  } catch (err) {
    mensagem.style.display = 'block'
    mensagem.textContent = 'Erro ao carregar dados. Verifique a conexão.'
    console.error('Falha ao buscar dados:', err)
    return
  }

  if (!dados || dados.length === 0) {
    mensagem.style.display = 'block'
    mensagem.textContent =
      'Ainda não há dados suficientes para o período selecionado.'
    if (chart) {
      chart.destroy()
      chart = null
    }
    return
  }

  const modoTimestamp = PERIODOS[periodo]?.modoTimestamp ?? 'hora'

  containerGrafico.style.display = 'block'
  mensagem.style.display = 'none'

  const labels = dados.map((d) => formatarTimestamp(d.timestamp, modoTimestamp))
  const temperaturas = dados.map((d) => d.temperatura)
  const umidadeAr = dados.map((d) => d.umidade_ar)
  const umidadeSolo = dados.map((d) => d.umidade_solo)

  const ultimo = dados[dados.length - 1]

  document.getElementById('temperatura').textContent =
    `${ultimo.temperatura.toFixed(1).replace('.', ',')} °C`
  document.getElementById('umidadeAr').textContent =
    `${ultimo.umidade_ar.toFixed(1).replace('.', ',')} %`
  document.getElementById('umidadeSolo').textContent =
    `${ultimo.umidade_solo.toFixed(1).replace('.', ',')} %`
  document.getElementById('ultimaAtualizacao').textContent =
    `Última atualização: ${formatarTimestamp(ultimo.timestamp, 'completo')}`

  const media = (arr) =>
    arr.length ? arr.reduce((a, b) => a + b, 0) / arr.length : 0

  document.getElementById('mediaTemp').textContent =
    `${media(temperaturas).toFixed(1).replace('.', ',')} °C`
  document.getElementById('mediaHum').textContent =
    `${media(umidadeAr).toFixed(1).replace('.', ',')} %`
  document.getElementById('mediaSoil').textContent =
    `${media(umidadeSolo).toFixed(1).replace('.', ',')} %`

  const ctx = document.getElementById('grafico')

  if (!chart) {
    chart = new Chart(ctx, {
      type: 'line',
      data: {
        labels: [],
        datasets: [
          {
            label: 'Temperatura (°C)',
            data: [],
            borderColor: 'rgba(224, 92, 42, 0.9)',
            backgroundColor: 'rgba(224, 92, 42, 0.06)',
            borderWidth: 1.5,
            tension: 0.4,
            pointRadius: 0,
            pointHoverRadius: 4,
            fill: true,
          },
          {
            label: 'Umidade Ar (%)',
            data: [],
            borderColor: 'rgba(46, 125, 50, 0.9)',
            backgroundColor: 'rgba(46, 125, 50, 0.06)',
            borderWidth: 1.5,
            tension: 0.4,
            pointRadius: 0,
            pointHoverRadius: 4,
            fill: true,
          },
          {
            label: 'Umidade Solo (%)',
            data: [],
            borderColor: 'rgba(21, 101, 192, 0.9)',
            backgroundColor: 'rgba(21, 101, 192, 0.06)',
            borderWidth: 1.5,
            tension: 0.4,
            pointRadius: 0,
            pointHoverRadius: 4,
            fill: true,
          },
        ],
      },
      options: {
        responsive: true,
        interaction: { mode: 'index', intersect: false },
        plugins: {
          legend: {
            position: 'top',
            labels: {
              usePointStyle: true,
              pointStyle: 'line',
              boxWidth: 30,
              font: { family: "'DM Sans', sans-serif", size: 12 },
            },
          },
          title: { display: false },
        },
        scales: {
          x: {
            ticks: {
              maxTicksLimit: 8,
              font: { family: "'DM Sans', sans-serif", size: 11 },
              color: '#5a7060',
            },
            grid: { color: 'rgba(0,0,0,0.04)' },
          },
          y: {
            suggestedMin: 0,
            suggestedMax: 100,
            ticks: {
              font: { family: "'DM Sans', sans-serif", size: 11 },
              color: '#5a7060',
            },
            grid: { color: 'rgba(0,0,0,0.04)' },
          },
        },
      },
    })
  }

  chart.data.labels = labels
  chart.data.datasets[0].data = temperaturas
  chart.data.datasets[1].data = umidadeAr
  chart.data.datasets[2].data = umidadeSolo
  chart.update('none') // sem animação no refresh automático
}

// ── Ciclo de atualização (sem sobreposição) ─────────────────────────────────

async function cicloAtualizacao() {
  await atualizarBotoesDisponiveis()
  await carregarDados(periodoAtual)
  setTimeout(cicloAtualizacao, 5000)
}

// ── Helpers ─────────────────────────────────────────────────────────────────

function formatarTimestamp(timestamp, modo = 'hora') {
  const data = new Date(timestamp)
  if (modo === 'hora')
    return data.toLocaleTimeString('pt-BR', {
      hour: '2-digit',
      minute: '2-digit',
    })
  if (modo === 'completo')
    return `${data.toLocaleDateString('pt-BR')} às ${data.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}`
  if (modo === 'dia')
    return data.toLocaleDateString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
    })
  if (modo === 'mes')
    return data.toLocaleDateString('pt-BR', {
      month: '2-digit',
      year: 'numeric',
    })
}

// ── Inicialização ───────────────────────────────────────────────────────────

// Desabilita todos os botões imediatamente, antes mesmo do JS consultar o backend,
// para evitar o flash onde todos aparecem clicáveis
document.querySelectorAll('[data-periodo]').forEach((btn) => {
  btn.disabled = true
})

document.querySelectorAll('[data-periodo]').forEach((btn) => {
  btn.addEventListener('click', () => {
    if (!btn.disabled) carregarDados(btn.dataset.periodo)
  })
})

cicloAtualizacao()
