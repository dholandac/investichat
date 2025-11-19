from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Transaction, PortfolioSnapshot
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Transaction)
def create_portfolio_snapshot(sender, instance, created, **kwargs):
    """
    Cria um snapshot da carteira após cada transação.
    Limita a criação de snapshots para evitar muitos registros (máximo 1 por hora).
    """
    if created:
        portfolio = instance.portfolio
        
        # Verifica se já existe um snapshot recente (última hora)
        last_snapshot = PortfolioSnapshot.objects.filter(
            portfolio=portfolio
        ).order_by('-created_at').first()
        
        should_create = True
        if last_snapshot:
            time_diff = timezone.now() - last_snapshot.created_at
            # Cria snapshot apenas se passou mais de 1 hora desde o último
            if time_diff < timedelta(hours=1):
                should_create = False
        
        if should_create:
            try:
                total_value = portfolio.get_total_value()
                total_cost = portfolio.get_total_cost()
                profit_loss = portfolio.get_profit_loss()
                profit_loss_percent = portfolio.get_profit_loss_percent()
                
                # Só cria snapshot se houver valor (evita snapshots zerados)
                if total_value > 0 or total_cost > 0:
                    PortfolioSnapshot.objects.create(
                        portfolio=portfolio,
                        total_value=total_value,
                        total_cost=total_cost,
                        profit_loss=profit_loss,
                        profit_loss_percent=profit_loss_percent
                    )
                    logger.debug(f"Snapshot criado para portfolio {portfolio.id}: valor={total_value}, custo={total_cost}")
                else:
                    logger.debug(f"Snapshot não criado para portfolio {portfolio.id}: valores zerados")
            except Exception as e:
                # Se houver erro ao criar snapshot (ex: API indisponível), apenas loga
                # Não queremos que falhas na API impeçam a criação de transações
                logger.error(f"Erro ao criar snapshot para portfolio {portfolio.id}: {e}", exc_info=True)

