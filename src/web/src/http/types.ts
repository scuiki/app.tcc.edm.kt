import type { components } from './schema'

// Um DTO do backend pelo nome, lido do schema que o openapi-typescript gera
export type Schema<Name extends keyof components['schemas']> = components['schemas'][Name]
