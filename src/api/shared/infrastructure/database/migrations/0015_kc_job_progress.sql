-- Quantos itens do estágio atual já terminaram, e de quantos, para a tela mostrar 7 de 10
ALTER TABLE kc_job ADD COLUMN progress_done INTEGER;
ALTER TABLE kc_job ADD COLUMN progress_total INTEGER;
