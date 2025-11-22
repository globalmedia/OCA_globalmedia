# Efíbank Integration (Odoo 18.0) + OCA l10n_brazil

Integra PIX e boletos do Efíbank ao Odoo, com webhook seguro, conciliação automática e botões diretamente na fatura.

## Recursos
- Emissão de PIX (copia-e-cola e QR code, quando disponível)
- Emissão de boletos (link e PDF)
- Webhook seguro (cabeçalho X-EFI-Webhook-Secret)
- Conciliação automática de faturas
- Botões na fatura (Gerar PIX, Gerar Boleto, Abrir Pagamento Efíbank)

## Compatibilidade OCA l10n_brazil
- CPF/CNPJ via `l10n_br_cpf`, `l10n_br_cnpj`, `cnpj_cpf` e fallback em `vat`
- Endereço via `street_name`, `street_number`, `district` e fallback em `street/street2/zip/city/state`
- Nome legal via `legal_name` e fallback em `name`
