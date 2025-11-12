from django.core.management.base import BaseCommand
from appKairos.models import Mercado, Producto
from decimal import Decimal


class Command(BaseCommand):
    help = 'Carga datos iniciales de mercados y productos'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('Iniciando carga de datos...'))
        
        # Crear Mercados
        mercados_data = [
            {'nombre': 'Gold (XAUUSD)', 'codigo': 'XAAUSD', 'descripcion': 'Oro contra Dólar estadounidense'},
            {'nombre': 'NASDAQ', 'codigo': 'NasdaQ', 'descripcion': 'Índice NASDAQ Composite'},
            {'nombre': 'S&P 500', 'codigo': 'SP500', 'descripcion': 'Índice Standard & Poor\'s 500'},
        ]
        
        mercados_creados = {}
        for mercado_data in mercados_data:
            mercado, created = Mercado.objects.get_or_create(
                codigo=mercado_data['codigo'],
                defaults=mercado_data
            )
            mercados_creados[mercado.codigo] = mercado
            if created:
                self.stdout.write(self.style.SUCCESS(f'✓ Mercado creado: {mercado.nombre}'))
            else:
                self.stdout.write(f'  Mercado ya existe: {mercado.nombre}')
        
        # Crear Productos
        productos_data = [
            {
                'nombre': 'M.P.T MarketProThief',
                'codigo': 'MPT',
                'descripcion': 'Algoritmo multi-mercado que opera en oro, NASDAQ y S&P 500. Estrategia de momentum y aprovechamiento de volatilidad.',
                'mercados': ['XAAUSD', 'NasdaQ', 'SP500'],
            },
            {
                'nombre': 'GoldenRoad',
                'codigo': 'GOLDEN',
                'descripcion': 'Especializado en oro (XAUUSD). Aprovecha patrones históricos y correlaciones con divisas.',
                'mercados': ['XAAUSD'],
            },
            {
                'nombre': 'MultiMarkets',
                'codigo': 'MULTI',
                'descripcion': 'Diversificación en índices NASDAQ y S&P 500. Estrategia de seguimiento de tendencias institucionales.',
                'mercados': ['NasdaQ', 'SP500'],
            },
        ]
        
        for producto_data in productos_data:
            mercados_codigos = producto_data.pop('mercados')
            producto, created = Producto.objects.get_or_create(
                codigo=producto_data['codigo'],
                defaults=producto_data
            )
            
            # Asignar mercados
            for codigo in mercados_codigos:
                if codigo in mercados_creados:
                    producto.mercados.add(mercados_creados[codigo])
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'✓ Producto creado: {producto.nombre}'))
            else:
                self.stdout.write(f'  Producto ya existe: {producto.nombre}')
        
        self.stdout.write(self.style.SUCCESS('\n✓ Carga de datos completada exitosamente!'))