import './Breadcrumb.css'

export interface Crumb {
  label: string
  // Sem href o item é só texto, e o último é o lugar atual
  href?: string
}

// O caminho até aqui, com links de volta, repetindo o que o menu marca, e ele só navega
export function Breadcrumb({ items }: { items: Crumb[] }) {
  return (
    <nav aria-label="Caminho" className="breadcrumb">
      <ol className="breadcrumb__list">
        {items.map((item, index) => {
          const isCurrent = index === items.length - 1
          return (
            <li key={`${item.label}-${index}`} className="breadcrumb__item">
              {index > 0 ? (
                <span className="breadcrumb__separator" aria-hidden="true">
                  ›
                </span>
              ) : null}
              {item.href ? (
                <a href={`#${item.href}`}>{item.label}</a>
              ) : (
                <span
                  aria-current={isCurrent ? 'page' : undefined}
                  className={isCurrent ? 'breadcrumb__current' : undefined}
                >
                  {item.label}
                </span>
              )}
            </li>
          )
        })}
      </ol>
    </nav>
  )
}
