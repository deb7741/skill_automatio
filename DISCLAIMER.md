# Disclaimer

## Not affiliated with Cadence

This is an independent community project. It is not affiliated with, sponsored by or endorsed by Cadence Design Systems, Inc. Cadence, Virtuoso, Spectre, Xcelium, Spectre AMS Designer, ADE Explorer, ADE Assembler, ViVA, SimVision and related names are trademarks of Cadence Design Systems, Inc.

You need your own valid licenses to run any Cadence tool referenced here.

## No PDK / foundry content, ever

This repository must stay safe to publish. It does **not** and must **not** contain:

- Foundry model files, model card parameters, corner names tied to a specific process, or extracted values
- Device/cell names, layer names, layer maps, technology files, display files or rule decks (DRC/LVS/PEX) from any PDK
- Screenshots, logs or netlists that reveal any of the above
- Content from Cadence manuals copied verbatim beyond short quotations for commentary

Examples use only:

- Cadence's generic libraries shipped with Virtuoso (`analogLib`, `basic`, `ahdlLib`, `functional`)
- Ideal elements (resistor, capacitor, vsource, isource, ...) and Verilog-A/SystemVerilog models written for this repo
- Generic corner labels (`tt`, `ss`, `ff`, `slow`, `fast`) used only as *placeholders* for whatever your own PDK provides

If you adapt an example to a real PDK, keep that adapted copy in your company's private repository, **not here**.

## No warranty

The scripts are provided "as is" (see [LICENSE](LICENSE)). Always review a script before running it on production data, especially SKILL that writes to libraries. Keep backups / use your design-management system.

## Version accuracy

Content targets IC6.1.8 and is checked against IC23.1/IC25.1 where possible. Command options and SKILL functions change between releases; your installation's documentation (`cdnshelp`) is the authority.
