# Ícones do Aplicativo

Esta pasta deve conter os ícones do aplicativo nos seguintes formatos:

- `32x32.png` - Ícone 32x32 pixels
- `128x128.png` - Ícone 128x128 pixels
- `128x128@2x.png` - Ícone 128x128 pixels @2x
- `icon.icns` - Ícone para macOS
- `icon.ico` - Ícone para Windows

## Como gerar os ícones

1. Crie uma imagem PNG de alta qualidade (512x512 ou maior)
2. Use uma ferramenta online como:
   - https://icon.kitchen/
   - https://www.favicon-generator.org/
3. Ou use o comando Tauri:
   ```bash
   npm run tauri icon path/to/your/icon.png
   ```

## Ícones Temporários

Por enquanto, você pode usar ícones padrão ou criar ícones simples com um editor de imagem.
