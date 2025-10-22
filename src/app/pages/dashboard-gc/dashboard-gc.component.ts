import { Component, OnInit } from '@angular/core';
import { CommonModule, DatePipe, CurrencyPipe, DecimalPipe } from '@angular/common'; // Adicione CurrencyPipe, DecimalPipe
import { RouterLink } from '@angular/router';
import { GiftcardService, GiftCard } from '../../../services/giftcard.service';
import { NotificationService } from '../../../services/notification.service';
import { ConfirmationService } from '../../../services/confirmation.service';
import { FormsModule } from '@angular/forms';
import { OrderItem } from '../../models/order.model'; // Certifique-se que OrderItem é importado

@Component({
  selector: 'app-dashboard-gc',
  standalone: true,
  imports: [
      CommonModule,
      RouterLink,
      FormsModule,
      DatePipe,
      CurrencyPipe, // Adicione CurrencyPipe
      DecimalPipe // Adicione DecimalPipe (para number:'1.1-1')
    ],
  templateUrl: './dashboard-gc.component.html',
  styleUrls: ['./dashboard-gc.component.css']
})
export class DashboardGcComponent implements OnInit {
  activeComponent = 'componente1';

  myGiftCards: GiftCard[] = [];
  isLoading = true;

  // Propriedades para validação
  validationCode: string = '';
  validationResult: OrderItem | null = null;
  isValidating: boolean = false;
  isPopupVisible = false;

  // Propriedades para o histórico
  usedItemsHistory: OrderItem[] = [];
  isLoadingHistory: boolean = false;

  // --- DICIONÁRIO DE TRADUÇÕES ADICIONADO ---
  statusTranslations: { [key: string]: string } = {
    // Status do Pedido (se precisar no futuro)
    'APPROVED': 'Aprovado',
    'PENDING': 'Pendente',
    'REJECTED': 'Rejeitado',
    'EXPIRED': 'Expirado',
    'REFUNDED': 'Estornado',
    // Status do Item/Código
    'VALID': 'Válido',
    'USED': 'Utilizado',
    'PARTIALLY_USED': 'Parcialmente Utilizado'
  };
  // --- FIM DO DICIONÁRIO ---

  constructor(
    private giftcardService: GiftcardService,
    private notificationService: NotificationService,
    private confirmationService: ConfirmationService
  ) { }

  ngOnInit(): void {
    this.loadMyGiftCards();
    this.loadUsedItemsHistory();
  }

  // --- NOVA FUNÇÃO DE TRADUÇÃO ADICIONADA ---
  translateStatus(status: string): string {
    return this.statusTranslations[status] || status; // Retorna a tradução ou o status original
  }
  // --- FIM DA FUNÇÃO ---

  showComponent(name: string) {
    this.activeComponent = name;
  }

  loadMyGiftCards(): void {
    this.isLoading = true;
    this.giftcardService.getMyGiftCards().subscribe({
      next: (data) => {
        this.myGiftCards = data;
        this.isLoading = false;
      },
      error: () => {
        this.notificationService.show('Não foi possível carregar seus gift cards.', 'error');
        this.isLoading = false;
      }
    });
  }

  deleteGiftCard(id: string, title: string): void {
    this.confirmationService.confirm({
      title: 'Confirmação de Exclusão',
      message: `Tem certeza que deseja excluir o gift card "${title}"?`,
      confirmText: 'Excluir',
      cancelText: 'Manter'
    }).subscribe(confirmed => {
      if (confirmed) {
        this.giftcardService.deleteGiftCard(id).subscribe({
          next: () => {
            this.notificationService.show('Gift card excluído!', 'success');
            this.myGiftCards = this.myGiftCards.filter(gc => gc.id !== id);
          },
          error: () => {
            this.notificationService.show('Falha ao excluir o gift card.', 'error');
          }
        });
      }
    });
  }

  loadUsedItemsHistory(): void {
    this.isLoadingHistory = true;
    this.giftcardService.getUsedGiftCardsHistory().subscribe({
      next: (data) => {
        // Ordena por data mais recente (se created_at existir em order)
        this.usedItemsHistory = data.sort((a, b) =>
           new Date(b.order?.created_at || 0).getTime() - new Date(a.order?.created_at || 0).getTime()
        );
        this.isLoadingHistory = false;
      },
      error: () => {
        this.notificationService.show('Não foi possível carregar o histórico.', 'error');
        this.isLoadingHistory = false;
      }
    });
  }

  validateCode(): void {
    if (!this.validationCode.trim()) {
      this.notificationService.show('Por favor, insira um código.', 'warning');
      return;
    }
    this.isValidating = true;

    this.giftcardService.validateGiftCardCode(this.validationCode).subscribe({
      next: (data) => {
        this.validationResult = data;
        this.isPopupVisible = true;
        this.isValidating = false;
      },
      error: (err) => {
        this.notificationService.show(err.error.detail || 'Código inválido ou não pertence à sua empresa.', 'error');
        this.isValidating = false;
      }
    });
  }

  markAsUsed(): void {
    if (!this.validationResult || this.validationResult.status !== 'VALID') {
        this.notificationService.show('Apenas códigos válidos podem ser marcados como usados.', 'warning');
        return;
    };

    // Usa o código que foi validado com sucesso
    const codeToMark = this.validationCode;

    this.giftcardService.markGiftCardCodeAsUsed(codeToMark).subscribe({
      next: (updatedItem) => { // A API retorna o item atualizado
        this.notificationService.show(`Código ${codeToMark} marcado como utilizado!`, 'success');
        this.closePopup(); // Fecha o popup
        this.loadUsedItemsHistory(); // Recarrega o histórico para refletir a mudança
      },
      error: (err) => {
        this.notificationService.show(err.error.detail || 'Erro ao marcar código como usado.', 'error');
        // Não fecha o popup em caso de erro para o usuário ver os detalhes
      }
    });
  }

  closePopup(): void {
    this.isPopupVisible = false;
    this.validationResult = null;
    this.validationCode = ''; // Limpa o campo do código
  }
}
