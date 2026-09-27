import '@testing-library/jest-dom'
import { vi } from 'vitest'

// O jsdom não tem canvas, então o gráfico vira vazio e o teste lê a tabela oculta ao lado dele
vi.mock('react-chartjs-2', () => ({ Line: () => null }))

// O jsdom não implementa o showModal e o close do dialog, então o teste usa o atributo open
if (!HTMLDialogElement.prototype.showModal) {
  HTMLDialogElement.prototype.showModal = function showModal(this: HTMLDialogElement) {
    this.setAttribute('open', '')
  }
  HTMLDialogElement.prototype.close = function close(this: HTMLDialogElement) {
    this.removeAttribute('open')
    this.dispatchEvent(new Event('close'))
  }
}
