"""Seed Canonical ApexPrint Knowledge Base Documents and Index into ChromaDB & BM25.

Populates 9 comprehensive enterprise support documents across 4 categories:
- product_manual: ProX-400, ColorWave-850, EcoTank L3150
- troubleshooting: Error codes (E-101, E-204, E-301, E-305), Wi-Fi & Static IP
- warranty: 1-Year Limited Warranty, RMA Procedure, Exclusions, Voltage & Tampering
- faq: AirPrint, Mopria, Bluetooth limitations, Toner Replacement, Drum Life
"""

import os
import sys
from pathlib import Path

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

DOCUMENTS = {
    ("product_manual", "apexprint_prox400_user_manual.md"): """# ApexPrint ProX-400 Enterprise Monochrome Laser Printer
**Document Type**: Official Product Manual & User Guide
**Model**: ProX-400 (Monochrome Desktop Laser Workgroup Printer)

## 1. Specifications and Hardware Capabilities
The ApexPrint ProX-400 is an enterprise-grade desktop monochrome laser printer designed for demanding small-to-medium workgroup environments.
- **Print Speed**: Up to 45 pages per minute (ppm) for letter-size monochrome documents. First page out time (FPOT) is approximately 5.2 seconds from ready mode.
- **Print Resolution**: True optical resolution of 1200 x 1200 dpi with 2400-class image enhancement smoothing technology.
- **Processor & Memory**: 1.2 GHz dual-core ARM processor with 1 GB standard memory (expandable up to 2.5 GB via DDR3 SO-DIMM slot).
- **Duplex Printing**: Standard automatic two-sided (duplex) printing supported up to 36 ppm.
- **Monthly Duty Cycle**: Maximum monthly volume of up to 100,000 pages per month; recommended monthly page volume is 3,000 to 10,000 pages.

## 2. Media Handling, Trays, and Paper Weights
- **Tray 1 (Multipurpose Bypass Tray)**: 100-sheet capacity. Supports standard paper, heavy cardstock, envelopes (No. 10, DL, C5), and glossy labels ranging from 60 g/m² to 220 g/m² (16 lb bond to 58 lb bond / 80 lb cover).
- **Tray 2 (Main Lower Paper Cassette)**: 500-sheet capacity. Accepts plain paper, recycled paper, and standard bond ranging from 60 g/m² to 120 g/m² (16 lb bond to 32 lb bond).
- **Optional Lower Feeder (Tray 3)**: Optional 550-sheet locking paper drawer supporting up to 120 gsm media.
- **Output Bin Capacity**: 250 sheets face-down with full bin detection sensor.

## 3. Electrical & Environmental Specifications
- **Voltage Requirements**: North American model requires 110V - 127V AC (+/- 10%), 50/60 Hz (+/- 3 Hz), 7.0 Amperes. European model (ProX-400E) requires 220V - 240V AC. Warning: Connecting a 110V model directly to 220V power without a step-down transformer will destroy the low-voltage power supply and immediately void the warranty.
- **Power Consumption**: Active Printing: 480 Watts; Standby / Ready Mode: 8.5 Watts; Energy Star Sleep Mode: 1.2 Watts.
- **Operating Environment**: Temperature: 10°C to 32.5°C (50°F to 90.5°F); Relative Humidity: 20% to 80% non-condensing.
""",

    ("product_manual", "apexprint_colorwave850_user_manual.md"): """# ApexPrint ColorWave-850 Wide-Format Inkjet Multi-Function System
**Document Type**: Official Product Manual & User Guide
**Model**: ColorWave-850 (Color Wide-Format Multi-Function System)

## 1. Printing Capabilities and Ink Delivery
The ApexPrint ColorWave-850 is a wide-format color inkjet multi-function system engineered for architectural drafts, commercial marketing, and color proofs.
- **Print Speed**: 35 pages per minute (ppm) for color documents; 40 pages per minute (ppm) for monochrome text.
- **Ink System**: Four individual high-capacity CMYK ink tanks (Cyan, Magenta, Yellow, Black) with automatic anti-clog maintenance cycles and integrated vacuum-sealed fluidics.
- **Print Resolution**: Up to 4800 x 1200 optimized dpi on photo and coated fine art media.
- **Color Management**: Built-in spectrophotometer sensor for automated ICC color profile calibration and Pantone spot color emulation.

## 2. Scanning, Duplexing, and Document Feeding
- **Automatic Duplex Scanning**: Supports automatic two-sided scanning and copying standard.
- **Document Feeder**: Equipped with a Dual-head Single-Pass Auto Document Feeder (RADF) holding up to 50 originals.
- **Scan Resolution**: Optical scanner resolution of 600 x 600 dpi; interpolated digital resolution up to 19200 dpi.
- **Media Support**: Accommodates media from 4x6 inches up to A3+ (13x19 inches wide-format) and banner lengths up to 47.2 inches (1200 mm).
""",

    ("product_manual", "apexprint_ecotank_l3150_specs.txt"): """# ApexPrint EcoTank L3150 All-in-One Ink Tank System
Document Type: Technical Specifications Sheet
Model: EcoTank L3150 / L300 Series

Key Hardware Specifications:
- Functionality: Print, Scan, Copy, Wireless Wi-Fi Direct.
- Yield: High-capacity spill-free ink refill bottles yield up to 4,500 black pages and 7,500 color pages per bottle set.
- Print Speed: 33 ppm draft black, 15 ppm draft color; ISO 24734 speed: 10 ipm black, 5.0 ipm color.
- Print Resolution: 5760 x 1440 optimized dpi using Variable-Sized Droplet Technology (VSDT).
- Mobile Connectivity: Supports Apple AirPrint, Mopria Print Service, ApexPrint Smart Panel App, and Wi-Fi Direct peer-to-peer connection.
- Standard Warranty: 12 months or 30,000 pages, whichever comes first.
""",

    ("troubleshooting", "apexprint_error_codes_and_hardware_troubleshooting.md"): """# ApexPrint Hardware Error Codes and Diagnostic Troubleshooting Guide
**Document Type**: Technical Service & Troubleshooting Manual
**Applies To**: ApexPrint ProX-400, ColorWave-850, EcoTank Series

## 1. Error Code E-101: Paper Jam Sequence
**Trigger**: Media failed to actuate paper path registration sensors within expected timing parameters.
**Resolution Steps**:
1. Power off the printer using the front power switch.
2. Open Front Access Door A and Rear Duplex Access Door B.
3. Inspect Tray 1 and Tray 2 feed areas. Gently grasp the jammed sheet with both hands and pull slowly in the direction of the paper path to avoid tearing.
4. Check internal feed rollers for torn scraps or foreign debris. Clean the rubber pickup rollers using a lint-free microfiber cloth lightly moistened with isopropyl alcohol.
5. Close all access doors securely, verify paper is aligned beneath max fill tabs in Tray 2, and power cycle the printer.

## 2. Error Code E-204: Fuser Unit Overheat Protection
**Trigger**: Fuser assembly thermistor sensed temperatures exceeding 230°C (446°F), engaging emergency thermal shutdown.
**Resolution Steps**:
1. Immediately power off the printer and disconnect the AC power cord from the wall outlet.
2. Allow the printer to cool down completely for at least 30 to 45 minutes before attempting any inspection.
3. Verify that all external ventilation louvers and rear exhaust vents are clear of obstructions and dust build-up.
4. Warning: Do NOT attempt to disassemble the fuser assembly using a screwdriver or tools. Opening internal high-voltage or thermal assemblies voids warranty and risks severe electrical shock or burn injury.
5. Reconnect power directly to a wall receptacle (avoid unrated power strips) and power on. If E-204 recurs immediately, contact an authorized ApexPrint service center for fuser replacement.

## 3. Error Code E-301 & E-305 Diagnostics
- **Error E-301**: Network adapter initialization failure or wireless transceiver lockup. Perform network reset via control panel.
- **Error E-305**: Optical Scanner Carriage Calibration Failure. Occurs on ColorWave-850 when scanner carriage cannot locate home position white balance strip. Power cycle unit and ensure flatbed platen glass is clean.
""",

    ("troubleshooting", "apexprint_prox400_wifi_and_connectivity_troubleshooting.md"): """# ApexPrint ProX-400 Wi-Fi and Network Connectivity Guide
**Document Type**: Connectivity & Network Administration Guide
**Model**: ProX-400 Series

## 1. Wi-Fi Setup and Connection Troubleshooting
- **WPS Push-Button Setup**: Press the WPS button on your Wi-Fi router. Within 2 minutes, press and hold the Wireless button on the printer control panel for 3 seconds until the Wi-Fi LED begins flashing green. The LED turns solid blue when connected.
- **Manual Wireless Setup Wizard**: On the LCD control panel, navigate to: `Settings` -> `Network Settings` -> `Wireless Setup Wizard`. Select your Network SSID from the detected broadcast list and input the WPA2/WPA3 passphrase using the navigation keypad.
- **Dual-Band Support**: ProX-400 supports both 2.4 GHz (802.11b/g/n) and 5.0 GHz (802.11a/n/ac) bands. Ensure router band steering assigns the printer to a stable frequency.

## 2. Static IP Address Configuration & 802.1x Enterprise Security
- **Static IPv4 Configuration**: Access the printer's Embedded Web Server (EWS) by typing its current DHCP IP address into a web browser, or navigate on the printer display to: `Settings` -> `Network` -> `TCP/IP Configuration` -> `Manual (Static)`.
  - IP Address: e.g., `192.168.1.150`
  - Subnet Mask: `255.255.255.0`
  - Gateway: `192.168.1.1`
  - Primary DNS: `8.8.8.8` (or internal company DNS server).
- **Enterprise 802.1x Network Security**: ProX-400 natively supports 802.1x EAP-TLS and PEAP authentication for enterprise networks without requiring additional software downloads. Configuring 802.1x authentication adheres strictly to enterprise guidelines and does NOT void the warranty or service agreements.
- **Network Adapter Factory Reset**: To reset network adapter to factory defaults, press and hold the `Go` and `Cancel` buttons simultaneously for 10 seconds while powering on until the network status LED blinks orange three times.
""",

    ("warranty", "apexprint_standard_limited_warranty_policy.md"): """# ApexPrint Standard Limited Hardware Warranty Policy
**Document Type**: Official Commercial Warranty Agreement
**Term**: 12 Months (1 Year) Limited Hardware Warranty

## 1. General Hardware Coverage Terms
ApexPrint warrants to the original end-user purchaser that the hardware products (including ProX-400, ColorWave-850, and EcoTank models) will be free from defects in materials and manufacturing workmanship for a period of twelve (12) months from the confirmed date of purchase.
- **Included Parts & Service**: Under this standard warranty, ApexPrint will, at its option, repair the product or replace defective hardware components with new or factory-reconditioned genuine OEM parts at zero cost for parts or labor.
- **Covered Assemblies**: Includes laser optical scanner assembly, formatter logic board, low-voltage power supply, paper drive gear motors, and internal sensors.

## 2. Return Merchandise Authorization (RMA) Procedure
To initiate a valid warranty claim:
1. Retain dated proof of purchase (original sales receipt, vendor invoice, or packing slip).
2. Contact ApexPrint Technical Support or submit a ticket via the support portal to troubleshoot and receive an authorized RMA number.
3. Package the unit in its original packaging or suitable protective shipping carton. Clearly mark the RMA number on the exterior shipping label.
4. ApexPrint covers prepaid ground return shipping for all approved RMA claims within the 12-month coverage window.
""",

    ("warranty", "apexprint_extended_warranty_and_exclusions.md"): """# ApexPrint Warranty Exclusions, Service Limitations, and Voiding Conditions
**Document Type**: Policy Addendum — Warranty Limitations & Exclusions

## 1. Excluded Wear Items and Consumables
The standard limited hardware warranty does not cover:
- Consumable items, including toner cartridges, ink bottles, drum units, waste toner collection boxes, and maintenance boxes.
- Normal wear-and-tear items subject to periodic friction exhaustion, such as rubber paper pickup rollers and separation pads beyond 90 days from purchase.

## 2. Explicit Warranty Voiding Conditions
The warranty shall be immediately voided under the following circumstances:
- **Physical Damage and Spills**: Damage caused by drops, impacts, liquid spills, physical abuse, or operating outside rated temperature and humidity specifications.
- **Incorrect Line Voltage**: Connecting a 110V rated unit directly into a 220V/240V AC power source without a certified step-down transformer.
- **Unauthorized Tampering and Disassembly**: Any disassembly, component replacement, or repair attempted by non-certified technicians, including attempting to open internal fuser or laser optics with hand tools.
- **Third-Party Supplies Policy**: The mere installation of third-party or refilled toner cartridges does not automatically void the printer's overall hardware warranty for unrelated failures. However, any physical damage, printhead corrosion, or fuser coating destruction directly caused by non-genuine or leaking third-party supplies is strictly excluded from warranty coverage.
""",

    ("faq", "apexprint_frequently_asked_questions_general.md"): """# ApexPrint General Support Frequently Asked Questions (FAQ)
**Document Type**: Customer Support Knowledge Base FAQ

## 1. Mobile & Wireless Printing Support
- **Q: Can I print directly from my Apple iPhone or iPad?**
  - **A**: Yes. The ApexPrint ProX-400 and ColorWave-850 natively support Apple AirPrint. Connect your iOS device to the same Wi-Fi network as the printer, tap the Share icon in any app, select Print, and choose your ApexPrint printer. No additional drivers or apps are required.
- **Q: Can I print from Android devices?**
  - **A**: Yes. Devices running Android 8.0 or later can print directly using the pre-installed Mopria Print Service or the free ApexPrint Mobile Connect app available on Google Play.

## 2. Bluetooth and Audio Streaming Limitations
- **Q: Can I connect my iPhone or smartphone via Bluetooth to stream audio or music to the printer?**
  - **A**: No. ApexPrint printers do not contain audio speakers, sound amplifiers, or multimedia audio Bluetooth profiles (A2DP). The integrated Bluetooth Low Energy (BLE) hardware is strictly limited to initial wireless network commissioning and beaconing. Insufficient hardware exists for audio streaming.

## 3. Firmware Update Procedures
- **Q: How do I update the printer firmware?**
  - **A**: Automatic Over-The-Air (OTA) updates can be enabled via `Settings` -> `System` -> `Firmware Update` -> `Auto-Check: Enabled`. Alternatively, download the latest `.bin` firmware file from the ApexPrint support portal, copy it to the root directory of a FAT32-formatted USB thumb drive, insert it into the front USB port, and select `Update from USB` on the control panel.
""",

    ("faq", "apexprint_frequently_asked_questions_hardware_and_service.md"): """# ApexPrint Hardware Service & Maintenance Frequently Asked Questions
**Document Type**: Service & Supplies FAQ

## 1. Toner Cartridge Replacement Procedure
- **Q: How do I replace the toner cartridge on the ProX-400?**
  - **A**:
    1. Open the front access door A.
    2. Pull the green cartridge release lever and slide the exhausted toner cartridge straight out along the guide rails.
    3. Remove the new genuine ApexPrint toner cartridge from its protective bag.
    4. Gently shake the cartridge horizontally 5 to 6 times to evenly distribute the toner powder within the hopper.
    5. Remove the orange protective shipping cover and pull the plastic sealing tape tab straight out until completely removed.
    6. Align the cartridge with the internal tracks and push firmly until it clicks into locked position.
    7. Close front door A and verify the status LED illuminates solid green.

## 2. Imaging Drum Unit Lifespan & Yield
- **Q: What is the rated lifespan of the imaging drum unit in the ProX-400?**
  - **A**: The separate long-life OPC imaging drum unit (Part # AP-DR400) is rated for approximately 30,000 standard pages at 5% ISO/IEC page coverage. The printer will display a 'Drum Unit Near End of Life' advisory message when 10% remaining capacity is reached.

## 3. Factory Reset Procedure
- **Q: How do I perform a complete factory restore?**
  - **A**: To perform a factory reset on the ApexPrint ProX-400, power off the unit, hold the power button for 10 seconds until the status LED flashes orange, then release. This restores all factory NVRAM defaults.
""",
}


def seed_knowledge_base():
    """Create document files on disk, chunk them, and index into ChromaDB & BM25."""
    kb_dir = PROJECT_ROOT / "data" / "knowledge_base"
    kb_dir.mkdir(parents=True, exist_ok=True)

    from app.ingestion.loader import DocumentLoader
    from app.ingestion.chunker import DocumentChunker, TextChunk
    from app.retrieval.vector_store import VectorStoreRetriever
    from app.retrieval.bm25 import BM25Retriever
    from app.core.config import settings

    loader = DocumentLoader()
    chunker = DocumentChunker()
    all_chunks = []

    print(f"Creating {len(DOCUMENTS)} canonical documents in {kb_dir}...")
    for (category, filename), content in DOCUMENTS.items():
        cat_dir = kb_dir / category
        cat_dir.mkdir(parents=True, exist_ok=True)
        file_path = cat_dir / filename
        file_path.write_text(content, encoding="utf-8")
        print(f"  [+] Wrote {file_path.relative_to(PROJECT_ROOT)} ({len(content)} chars)")

        doc = loader.load_file(file_path, category=category)
        chunks = chunker.chunk_document(doc)
        all_chunks.extend(chunks)
        print(f"      Extracted {len(chunks)} chunks.")

    print(f"\nTotal canonical chunks extracted: {len(all_chunks)}")

    # Index into ChromaDB
    print("\nIndexing chunks into ChromaDB persistent collection...")
    try:
        import chromadb
        client = chromadb.PersistentClient(path=settings.LOCAL_EPHEMERAL_CHROMA_DIR)
        collection = client.get_or_create_collection(
            name=settings.CHROMA_COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
        # Prepare data for Chroma upsert
        c_ids = [c.chunk_id for c in all_chunks]
        c_texts = [c.text for c in all_chunks]
        c_metas = []
        for c in all_chunks:
            meta = {
                "chunk_id": c.chunk_id,
                "document_id": c.document_id,
                "category": c.category,
                "source": c.source,
                "filename": c.source,
                "page_number": c.page_number,
                "content_hash": c.content_hash,
                "is_mock": False,
            }
            c_metas.append(meta)

        collection.upsert(
            ids=c_ids,
            documents=c_texts,
            metadatas=c_metas,
        )
        print(f"Successfully upserted {len(all_chunks)} chunks into ChromaDB! Total collection count: {collection.count()}")
    except Exception as e:
        print(f"Warning: Could not index to ChromaDB: {e}")

    # Verify retrieval
    print("\nVerifying live retrieval...")
    v_retriever = VectorStoreRetriever(allow_mock=False)
    results = v_retriever.retrieve("What is the print speed of the ProX-400?", top_k=2)
    print(f"Retrieved {len(results)} chunks for print speed query:")
    for r in results:
        print(f"  - [{r.metadata.get('category')}] {r.source}: Score {round(r.score, 3)} | {r.text[:90]}...")

    print("\nCanonical Knowledge Base seeding complete!")
    return len(all_chunks)


if __name__ == "__main__":
    seed_knowledge_base()
