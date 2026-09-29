"""Generate fictional sample CVs from the one-slide template of Markus_Mustermann_-_202501.pptx.

Only text is replaced; layout, fonts and the avatar stay as in the template.
Usage: python3 samples/make_sample_cvs.py samples/cvs/Markus_Mustermann_-_202501.pptx samples/cvs
"""
import copy
import re
import sys
import zipfile
from pathlib import Path
from xml.dom import minidom

B = "•    "

PEOPLE = [
    {
        "file": "Sophie_Keller_-_202606.pptx", "date": "2026-06-12",
        "name": "Sophie Keller", "title": "Senior Full Stack Developer & Data Engineer", "email": "sophie@mycv.com",
        "expertise": ["Full Stack Development", "Data Pipelines, ETL/ELT", "Java 17, Python", "Spring Boot, FastAPI",
                      "Angular, TypeScript, RxJS", "Apache Spark, PySpark, Databricks", "REST, OpenAPI, GraphQL",
                      "Docker, Kubernetes, Azure", "GitLab CI, Merge Requests, Code Reviews", "GitHub Copilot, AI-assisted testing",
                      "PostgreSQL, Delta Lake", "Scrum, Kanban"],
        "industries": ["Insurance", "Banking", "Retail"],
        "background": "Sophie is a **senior full stack developer** with **11 years of experience** building web applications and data platforms. She combines **Java and Angular** development with **data engineering on Spark and Databricks**, and has delivered end-to-end solutions from ingestion pipelines to customer-facing portals. As a **technical lead**, she coaches teams on clean code, code reviews and test automation, and introduced **AI-assisted development tooling** across the SDLC in her last two projects.",
        "certs": ["Databricks Certified Data Engineer Associate", "Microsoft Certified: Azure Developer Associate (AZ-204)", "Professional Scrum Master I"],
        "languages": ["German (Native)", "English (C1)", "French (B1)"],
        "projects": [
            ("Swiss Insurance Group, Zurich - Technical Lead Full Stack (03/2022 – Current)", [
                "Lead a team of 6 developers building a claims portal with Angular and Spring Boot microservices.",
                "Designed ETL pipelines in PySpark on Databricks feeding the claims data warehouse.",
                "Introduced GitHub Copilot and AI-generated unit tests, raising test coverage from 55% to 80%.",
                "Technology Stack: Java 17, Spring Boot, Angular 15, TypeScript, PySpark, Databricks, Azure, AKS"]),
            ("Private Bank, Geneva - Senior Full Stack Developer (01/2019 – 02/2022)", [
                "Developed REST APIs and an Angular front end for a portfolio reporting platform.",
                "Built nightly batch jobs with Spark SQL for performance calculations.",
                "Technology Stack: Java 11, Spring Boot, Angular, Spark SQL, Oracle, OpenShift, GitLab"]),
            ("Retail Company, Basel - Software Developer (09/2013 – 12/2018)", [
                "Developed and maintained the web shop back end and product data interfaces.",
                "Technology Stack: Java, Spring, JavaScript, MySQL, Jenkins, Git"]),
        ],
    },
    {
        "file": "Lukas_Braendle_2026-03.pptx", "date": "2026-03-10",
        "name": "Lukas Brändle", "title": "Data Engineer", "email": "lukas@mycv.com",
        "expertise": ["Data Engineering", "Python, SQL", "Apache Spark, PySpark, Spark SQL", "Airflow, dbt",
                      "ETL/ELT Processes", "Azure Data Factory, Synapse", "Kafka, Event Streaming", "Docker, Kubernetes",
                      "Git, Pull Requests", "Data Modelling"],
        "industries": ["Telecommunications", "Energy", "Public Sector"],
        "background": "Lukas is a **data engineer** with **7 years of experience** designing and operating **batch and streaming data pipelines**. He has built data platforms on **Azure** and on-premise Kubernetes clusters, using **Spark, Airflow and dbt** to deliver reliable data products for analytics and reporting teams. Lukas works closely with business stakeholders to translate reporting needs into robust data models.",
        "certs": ["Microsoft Certified: Azure Data Engineer Associate (DP-203)", "Certified Kubernetes Application Developer (CKAD)"],
        "languages": ["German (Native)", "English (C1)"],
        "projects": [
            ("Swiss Telecom Provider, Bern - Senior Data Engineer (04/2022 – Current)", [
                "Designed and implemented data pipelines for network usage data processing 2 TB per day.",
                "Migrated legacy ETL jobs to PySpark and Airflow on Kubernetes.",
                "Technology Stack: Python, PySpark, Spark SQL, Airflow, dbt, Kafka, Kubernetes, PostgreSQL"]),
            ("Energy Utility, Zurich - Data Engineer (01/2020 – 03/2022)", [
                "Built ELT processes in Azure Data Factory and Synapse for smart meter data.",
                "Developed small REST services in Python (Flask) to expose data products.",
                "Technology Stack: Python, Azure Data Factory, Synapse, Flask, Azure DevOps"]),
            ("Canton Administration, Aarau - BI Developer (02/2018 – 12/2019)", [
                "Developed reporting data marts and SQL-based ETL processes.",
                "Technology Stack: SQL Server, SSIS, Power BI"]),
        ],
    },
    {
        "file": "Aylin_Demir_-_202609.pptx", "date": "2026-09-04",
        "name": "Aylin Demir", "title": "Full Stack Developer", "email": "aylin@mycv.com",
        "expertise": ["Full Stack Web Development", "Python, Django, FastAPI", "TypeScript, Angular", "REST APIs, OpenAPI",
                      "Docker, AWS (ECS, Lambda)", "GitHub, Pull Requests, Code Reviews", "Claude Code, GitHub Copilot",
                      "PostgreSQL, Redis", "Test Automation (pytest, Cypress)", "Agile (Scrum)"],
        "industries": ["E-Commerce", "Healthcare", "Logistics"],
        "background": "Aylin is a **full stack developer** with **6 years of experience** delivering web applications with **Python back ends and Angular front ends**. She has a strong focus on **API design** and **test automation**, and uses **AI coding assistants throughout the SDLC**, from generating tests to reviewing pull requests. Aylin enjoys working in cross-functional teams and has onboarded and mentored junior developers.",
        "certs": ["AWS Certified Developer - Associate", "Professional Scrum Developer I"],
        "languages": ["Turkish (Native)", "German (C2)", "English (C1)"],
        "projects": [
            ("Online Pharmacy, Zurich - Full Stack Developer (06/2023 – 08/2026)", [
                "Developed the prescription upload and order tracking features with FastAPI and Angular.",
                "Introduced Claude Code and GitHub Copilot for test generation and pull request reviews in the team.",
                "Technology Stack: Python, FastAPI, Angular 16, TypeScript, PostgreSQL, Docker, AWS ECS, GitHub Actions"]),
            ("Logistics Company, Basel - Full Stack Developer (03/2021 – 05/2023)", [
                "Built REST APIs for shipment tracking and an Angular dashboard for dispatchers.",
                "Wrote ETL scripts in Python to load partner data into the tracking database.",
                "Technology Stack: Python, Django, Django REST Framework, Angular, PostgreSQL, Redis"]),
            ("Web Agency, Winterthur - Junior Developer (09/2019 – 02/2021)", [
                "Developed customer websites and small web applications.",
                "Technology Stack: Python, Django, JavaScript, Git"]),
        ],
    },
    {
        "file": "Tomasz_Nowak_-_04.2026.pptx", "date": "2026-04-20",
        "name": "Tomasz Nowak", "title": "Full Stack Java Developer", "email": "tomasz@mycv.com",
        "expertise": ["Full Stack Development", "Java, Kotlin", "Spring Boot, Quarkus", "Angular, React, TypeScript", "Microservices, REST, gRPC",
                      "Kafka, RabbitMQ", "OpenShift, Kubernetes, Helm", "GitLab, Merge Requests", "Oracle, PostgreSQL", "SAFe"],
        "industries": ["Banking", "Insurance"],
        "background": "Tomasz is a **full stack Java developer** with **7 years of experience** in **microservice architectures** for financial services. He has delivered **Spring Boot back ends with Angular and React front ends** running on OpenShift, and is experienced in **event-driven integration with Kafka**. Tomasz is known for his pragmatic approach and his attention to code quality and reviews.",
        "certs": ["Oracle Certified Professional: Java SE 17 Developer", "Red Hat Certified Specialist in OpenShift Application Development"],
        "languages": ["Polish (Native)", "English (C1)", "German (B1)"],
        "projects": [
            ("Major Swiss Bank, Zurich - Full Stack Developer (01/2022 – Current)", [
                "Developed microservices for payment processing with Spring Boot and Kafka.",
                "Built Angular and React/TypeScript front ends for payment operations teams.",
                "Technology Stack: Java 17, Spring Boot, Kafka, Angular, React, TypeScript, OpenShift, Helm, GitLab"]),
            ("Insurance Company, Warsaw - Java Developer (04/2017 – 12/2021)", [
                "Developed REST and SOAP web services for policy administration.",
                "Migrated monolith modules to Quarkus microservices.",
                "Technology Stack: Java 11, Spring, Quarkus, Oracle, Jenkins, Git"]),
        ],
    },
    {
        "file": "Elena_Rossi_-_202602.pptx", "date": "2026-02-03",
        "name": "Elena Rossi", "title": "Frontend Engineer", "email": "elena@mycv.com",
        "expertise": ["Frontend Development", "Angular, TypeScript, RxJS, NgRx", "React, Next.js", "Node.js, Express",
                      "REST API Integration", "UI/UX, Accessibility (WCAG)", "Jest, Cypress", "Git, GitHub, Code Reviews", "Figma"],
        "industries": ["Media", "Travel", "Public Sector"],
        "background": "Elena is a **frontend engineer** with **8 years of experience** building accessible, high-performance web applications with **Angular and React**. She works at the interface between design and development and has set up **component libraries and design systems** used by several teams. On the back end, Elena builds lightweight **Node.js** services for front-end integration.",
        "certs": ["Google UX Design Professional Certificate"],
        "languages": ["Italian (Native)", "English (C2)", "German (A2)"],
        "projects": [
            ("Swiss Travel Platform, Lucerne - Lead Frontend Engineer (05/2022 – 01/2026)", [
                "Built the booking front end in Angular with NgRx state management.",
                "Set up a shared component library and accessibility testing for three product teams.",
                "Technology Stack: Angular 15, TypeScript, NgRx, Node.js, Jest, Cypress, GitHub Actions"]),
            ("Media House, Milan - Frontend Developer (02/2017 – 04/2022)", [
                "Developed news portals and editorial tools in React and Next.js.",
                "Integrated REST APIs of the content management system.",
                "Technology Stack: React, Next.js, TypeScript, Node.js, Express, Git"]),
        ],
    },
    {
        "file": "David_Okafor_-_202511.pptx", "date": "2025-11-08",
        "name": "David Okafor", "title": "Backend & Data Integration Engineer", "email": "david@mycv.com",
        "expertise": ["Backend Development", "Java, Spring Boot", "Scala, Spark SQL", "ETL Processes, Azure Data Factory",
                      "REST APIs, SOAP Web Services", "Azure, Terraform", "Bitbucket, Pull Requests", "SQL Server, Oracle", "Integration Patterns"],
        "industries": ["Pharma", "Manufacturing", "Banking"],
        "background": "David is a **backend and data integration engineer** with **9 years of experience** connecting enterprise systems. He designs **REST and SOAP integrations** in Java and builds **data processing jobs in Scala and Spark SQL** on Azure. David has worked in regulated environments and is used to validated delivery processes.",
        "certs": ["Microsoft Certified: Azure Solutions Architect Expert", "HashiCorp Certified: Terraform Associate"],
        "languages": ["English (Native)", "German (C1)"],
        "projects": [
            ("Pharmaceutical Company, Basel - Senior Integration Engineer (02/2021 – Current)", [
                "Designed REST integrations between the LIMS and the ERP system with Spring Boot.",
                "Built Spark SQL jobs in Scala for batch processing of laboratory data on Azure.",
                "Technology Stack: Java 11, Spring Boot, Scala, Spark SQL, Azure Data Factory, Terraform, Bitbucket"]),
            ("Machine Manufacturer, Schaffhausen - Software Engineer (06/2015 – 01/2021)", [
                "Developed SOAP web services and ETL processes for production data.",
                "Technology Stack: Java, SOAP, SQL Server, SSIS, Jenkins"]),
        ],
    },
    {
        "file": "Julia_Hofmann_2026-08.pptx", "date": "2026-08-18",
        "name": "Julia Hofmann", "title": "Junior Full Stack Developer", "email": "julia@mycv.com",
        "expertise": ["Full Stack Development", "Python, FastAPI", "Angular, TypeScript", "REST APIs", "Docker",
                      "GitLab, Merge Requests", "PostgreSQL", "Scrum"],
        "industries": ["Insurance", "Education"],
        "background": "Julia is a **junior full stack developer** with **3 years of experience** after completing her M.Sc. in Computer Science. She develops **Python back ends and Angular front ends** and is eager to grow into data engineering. Julia is a reliable team member who takes ownership of features from design to deployment.",
        "certs": ["Professional Scrum Master I"],
        "languages": ["German (Native)", "English (B2)", "Spanish (B1)"],
        "projects": [
            ("Swiss Insurance Group, Zurich - Full Stack Developer (09/2023 – Current)", [
                "Developed features for the broker portal with FastAPI and Angular.",
                "Implemented REST endpoints and database migrations.",
                "Technology Stack: Python, FastAPI, Angular 15, TypeScript, PostgreSQL, Docker, GitLab CI"]),
            ("University of Zurich - Student Developer (03/2022 – 08/2023)", [
                "Developed a course registration web application.",
                "Technology Stack: Python, Flask, JavaScript, Git"]),
        ],
    },
    {
        "file": "Nikolai_Petrov_-_12.2022.pptx", "date": "2022-12-12",
        "name": "Nikolai Petrov", "title": "Test Automation Engineer", "email": "nikolai@mycv.com",
        "expertise": ["Test Automation", "Java, Selenium, Cucumber", "Playwright", "API Testing (Postman, REST Assured)",
                      "Performance Testing (JMeter)", "Jenkins, Git", "ISTQB Test Management", "Agile Testing"],
        "industries": ["Banking", "Telecommunications"],
        "background": "Nikolai is a **test automation engineer** with **10 years of experience** in quality assurance for large IT programmes. He builds **automated UI, API and performance test suites** and integrates them into CI/CD pipelines. Nikolai has led test teams of up to 8 testers and defined test strategies for release trains.",
        "certs": ["ISTQB Certified Tester Advanced Level - Test Manager", "ISTQB Certified Tester Foundation Level"],
        "languages": ["Bulgarian (Native)", "English (C1)", "German (C1)"],
        "projects": [
            ("Major Swiss Bank, Zurich - Test Lead (03/2019 – 11/2022)", [
                "Defined the test strategy for a release train of 5 teams.",
                "Built automated regression suites with Selenium, Cucumber and REST Assured.",
                "Technology Stack: Java, Selenium, Cucumber, REST Assured, JMeter, Jenkins, Git"]),
            ("Telecom Provider, Sofia - Test Automation Engineer (01/2013 – 02/2019)", [
                "Automated UI and API tests for self-service portals.",
                "Technology Stack: Java, Selenium, Postman, Jenkins"]),
        ],
    },
]


def texts_of(p):
    return "".join(t.firstChild.data if t.firstChild else "" for t in p.getElementsByTagName("a:t"))


def set_single_run(para, text, rpr_attrs=None):
    runs = para.getElementsByTagName("a:r")
    keep = runs[0]
    for r in list(runs[1:]):
        r.parentNode.removeChild(r)
    for tag in ("a:br", "a:fld"):
        for n in list(para.getElementsByTagName(tag)):
            n.parentNode.removeChild(n)
    t = keep.getElementsByTagName("a:t")[0]
    t.firstChild.data = text
    if text != text.strip():
        t.setAttribute("xml:space", "preserve")


def rebuild(tx_body, items):
    """items: list of (template_para, text) -> replace all paragraphs of the text body."""
    paras = tx_body.getElementsByTagName("a:p")
    new = []
    for tmpl, text in items:
        p = tmpl.cloneNode(True)
        set_single_run(p, text)
        new.append(p)
    for p in list(paras):
        tx_body.removeChild(p)
    for p in new:
        tx_body.appendChild(p)


def rich_para(tmpl_para, text):
    """Background paragraph: **bold** segments become bold runs."""
    p = tmpl_para.cloneNode(True)
    runs = p.getElementsByTagName("a:r")
    normal = next(r for r in runs if not r.getElementsByTagName("a:rPr") or r.getElementsByTagName("a:rPr")[0].getAttribute("b") != "1")
    bold = next(r for r in runs if r.getElementsByTagName("a:rPr") and r.getElementsByTagName("a:rPr")[0].getAttribute("b") == "1")
    normal, bold = normal.cloneNode(True), bold.cloneNode(True)
    for r in list(runs):
        p.removeChild(r)
    end = p.getElementsByTagName("a:endParaRPr")
    anchor = end[0] if end else None
    for i, seg in enumerate(re.split(r"\*\*", text)):
        if not seg:
            continue
        r = (bold if i % 2 else normal).cloneNode(True)
        t = r.getElementsByTagName("a:t")[0]
        t.firstChild.data = seg
        t.setAttribute("xml:space", "preserve")
        p.insertBefore(r, anchor) if anchor else p.appendChild(r)
    return p


def build(template: Path, out: Path, person: dict):
    zin = zipfile.ZipFile(template)
    doc = minidom.parseString(zin.read("ppt/slides/slide1.xml"))
    boxes = {}
    for sp in doc.getElementsByTagName("p:sp"):
        body = sp.getElementsByTagName("p:txBody")
        if not body:
            continue
        paras = body[0].getElementsByTagName("a:p")
        first = texts_of(paras[0]) if paras else ""
        boxes[first.split(":")[0].strip()] = (body[0], paras)

    def single(key, text):
        body, paras = boxes[key]
        rebuild(body, [(paras[0], text)])

    single("Markus Mustermann", person["name"])
    single(next(k for k in boxes if k.startswith("Solution")), person["title"])
    single("markus@mycv.com", person["email"])

    def listbox(key, entries):
        body, paras = boxes[key]
        bullet = next(p for p in paras[1:] if texts_of(p).startswith("•"))
        rebuild(body, [(paras[0], texts_of(paras[0]))] + [(bullet, B + e) for e in entries])

    listbox("Areas of Expertise", person["expertise"])
    listbox("Industries", person["industries"])
    listbox("Certifications", person["certs"])
    listbox("Languages", person["languages"])

    body, paras = boxes["Professional Background"]
    head = paras[0].cloneNode(True)
    rich = rich_para(paras[1], person["background"])
    for p in list(paras):
        body.removeChild(p)
    body.appendChild(head)
    body.appendChild(rich)

    body, paras = boxes["Relevant Project Experience"]
    proj_head = paras[1]
    bullet = next(p for p in paras[2:] if texts_of(p).startswith("•"))
    items = [(paras[0], texts_of(paras[0]))]
    for header, bullets in person["projects"]:
        items.append((proj_head, header))
        items += [(bullet, B + b) for b in bullets]
    rebuild(body, items)

    slide_xml = doc.toxml(encoding="UTF-8")
    if b'standalone="yes"' not in slide_xml[:100]:
        slide_xml = slide_xml.replace(b'<?xml version="1.0" encoding="UTF-8"?>',
                                      b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>', 1)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == "ppt/slides/slide1.xml":
                data = slide_xml
            elif item.filename == "docProps/core.xml":
                s = data.decode()
                s = re.sub(r"<cp:lastModifiedBy>.*?</cp:lastModifiedBy>", "<cp:lastModifiedBy></cp:lastModifiedBy>", s)
                s = re.sub(r"(<dcterms:modified[^>]*>)[^<]+", rf"\g<1>{person['date']}T09:00:00Z", s)
                s = re.sub(r"<dc:description>.*?</dc:description>", "<dc:description></dc:description>", s)
                data = s.encode()
            zout.writestr(item, data)


if __name__ == "__main__":
    template, out_dir = Path(sys.argv[1]), Path(sys.argv[2])
    out_dir.mkdir(parents=True, exist_ok=True)
    for person in PEOPLE:
        build(template, out_dir / person["file"], person)
        print("wrote", person["file"])
