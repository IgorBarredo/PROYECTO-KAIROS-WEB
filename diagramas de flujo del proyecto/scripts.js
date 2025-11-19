// Initialize Mermaid
mermaid.initialize({ 
    startOnLoad: true,
    theme: 'default',
    themeVariables: {
        primaryColor: '#0077b6',
        primaryTextColor: '#fff',
        primaryBorderColor: '#00b4d8',
        lineColor: '#00b4d8',
        secondaryColor: '#00ddff',
        tertiaryColor: '#90e0ef',
        background: '#ffffff',
        mainBkg: '#0077b6',
        secondBkg: '#00b4d8',
        tertiaryBkg: '#00ddff',
        textColor: '#333',
        fontSize: '16px'
    },
    flowchart: {
        useMaxWidth: true,
        htmlLabels: true,
        curve: 'basis'
    },
    sequence: {
        useMaxWidth: true,
        mirrorActors: true
    },
    er: {
        useMaxWidth: true
    }
});

// Smooth scroll for navigation links
document.addEventListener('DOMContentLoaded', function() {
    const navLinks = document.querySelectorAll('.nav-link');
    
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const targetId = this.getAttribute('href');
            const targetSection = document.querySelector(targetId);
            
            if (targetSection) {
                targetSection.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
                
                // Add active class
                navLinks.forEach(l => l.classList.remove('active'));
                this.classList.add('active');
            }
        });
    });
    
    // Highlight current section in navigation
    const sections = document.querySelectorAll('.section');
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const id = entry.target.getAttribute('id');
                navLinks.forEach(link => {
                    link.classList.remove('active');
                    if (link.getAttribute('href') === `#${id}`) {
                        link.classList.add('active');
                    }
                });
            }
        });
    }, {
        threshold: 0.3
    });
    
    sections.forEach(section => {
        observer.observe(section);
    });
    
    // Add animation to diagram cards on scroll
    const diagramCards = document.querySelectorAll('.diagram-card');
    const cardObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '0';
                entry.target.style.transform = 'translateY(20px)';
                setTimeout(() => {
                    entry.target.style.transition = 'all 0.6s ease';
                    entry.target.style.opacity = '1';
                    entry.target.style.transform = 'translateY(0)';
                }, 100);
            }
        });
    }, {
        threshold: 0.1
    });
    
    diagramCards.forEach(card => {
        cardObserver.observe(card);
    });
    
    // Print functionality
    const printBtn = document.createElement('button');
    printBtn.innerHTML = '🖨️ Imprimir Diagramas';
    printBtn.style.cssText = `
        position: fixed;
        bottom: 30px;
        right: 30px;
        padding: 15px 25px;
        background: linear-gradient(135deg, #0077b6 0%, #00b4d8 100%);
        color: white;
        border: none;
        border-radius: 50px;
        font-weight: 600;
        cursor: pointer;
        box-shadow: 0 4px 15px rgba(0, 119, 182, 0.4);
        transition: all 0.3s ease;
        z-index: 1000;
    `;
    
    printBtn.addEventListener('mouseenter', function() {
        this.style.background = 'linear-gradient(135deg, #00b4d8 0%, #00ddff 100%)';
        this.style.transform = 'translateY(-2px)';
        this.style.boxShadow = '0 6px 20px rgba(0, 221, 255, 0.5)';
    });
    
    printBtn.addEventListener('mouseleave', function() {
        this.style.background = 'linear-gradient(135deg, #0077b6 0%, #00b4d8 100%)';
        this.style.transform = 'translateY(0)';
        this.style.boxShadow = '0 4px 15px rgba(0, 119, 182, 0.4)';
    });
    
    printBtn.addEventListener('click', function() {
        window.print();
    });
    
    document.body.appendChild(printBtn);
    
    // Back to top button
    const backToTopBtn = document.createElement('button');
    backToTopBtn.innerHTML = '↑';
    backToTopBtn.style.cssText = `
        position: fixed;
        bottom: 90px;
        right: 30px;
        width: 50px;
        height: 50px;
        background: linear-gradient(135deg, #0077b6 0%, #00b4d8 100%);
        color: white;
        border: none;
        border-radius: 50%;
        font-size: 24px;
        cursor: pointer;
        box-shadow: 0 4px 15px rgba(0, 119, 182, 0.4);
        transition: all 0.3s ease;
        opacity: 0;
        visibility: hidden;
        z-index: 1000;
    `;
    
    window.addEventListener('scroll', function() {
        if (window.pageYOffset > 300) {
            backToTopBtn.style.opacity = '1';
            backToTopBtn.style.visibility = 'visible';
        } else {
            backToTopBtn.style.opacity = '0';
            backToTopBtn.style.visibility = 'hidden';
        }
    });
    
    backToTopBtn.addEventListener('mouseenter', function() {
        this.style.background = 'linear-gradient(135deg, #00b4d8 0%, #00ddff 100%)';
        this.style.transform = 'translateY(-2px)';
    });
    
    backToTopBtn.addEventListener('mouseleave', function() {
        this.style.background = 'linear-gradient(135deg, #0077b6 0%, #00b4d8 100%)';
        this.style.transform = 'translateY(0)';
    });
    
    backToTopBtn.addEventListener('click', function() {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    });
    
    document.body.appendChild(backToTopBtn);
    
    console.log('📊 Diagramas de Flujo - Proyecto Kairos cargados exitosamente');
    console.log('Total de secciones:', sections.length);
    console.log('Total de diagramas:', diagramCards.length);
});