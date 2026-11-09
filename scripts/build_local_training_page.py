"""Render the generic architecture from its tracked HTML template and Mermaid source."""
import argparse
import asyncio
from pathlib import Path

from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parent.parent


async def build(args):
    source = (ROOT / 'deliverables/architecture/local-training.mmd').read_text(encoding='utf-8')
    template = (ROOT / 'deliverables/architecture/local-training.template.html').read_text(encoding='utf-8')
    assert template.count('__DIAGRAM__') == 1
    async with async_playwright() as p:
        launch = {'headless': True}
        if args.browser:
            launch['executable_path'] = str(args.browser)
        browser = await p.chromium.launch(**launch)
        page = await browser.new_page()
        await page.goto('about:blank')
        await page.add_script_tag(path=str(args.mermaid_js.resolve()))
        await page.evaluate('''() => mermaid.initialize({startOnLoad:false,securityLevel:'strict',theme:'base',fontFamily:'PingFang SC,Microsoft YaHei,sans-serif',themeVariables:{fontSize:'16px',primaryColor:'#f0f3ee',primaryBorderColor:'#688574',primaryTextColor:'#21372f',lineColor:'#71877b',clusterBkg:'#fafbf8',clusterBorder:'#c3cfc2',edgeLabelBackground:'#ffffff'},flowchart:{htmlLabels:false,curve:'basis',nodeSpacing:25,rankSpacing:32}})''')
        svg = await page.evaluate('''async source => (await mermaid.render('local-training-diagram',source)).svg''', source)
        await browser.close()
    args.output.write_text(template.replace('__DIAGRAM__', svg), encoding='utf-8')
    print('Rendered architecture HTML: ' + str(args.output))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mermaid-js', type=Path, required=True)
    parser.add_argument('--browser', type=Path)
    parser.add_argument('--output', type=Path, default=ROOT / 'deliverables/architecture/local-training.html')
    asyncio.run(build(parser.parse_args()))


if __name__ == '__main__':
    main()
