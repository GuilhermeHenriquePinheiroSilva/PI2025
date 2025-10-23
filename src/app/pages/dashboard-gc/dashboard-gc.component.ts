import { Component, OnInit } from '@angular/core';
import { CommonModule, DatePipe, CurrencyPipe, DecimalPipe } from '@angular/common';
import { RouterLink } from '@angular/router';
import { GiftcardService, GiftCard } from '../../../services/giftcard.service';
import { NotificationService } from '../../../services/notification.service';
import { ConfirmationService } from '../../../services/confirmation.service';
import { FormsModule } from '@angular/forms';
import { OrderItem } from '../../models/order.model'; // Certifique-se que OrderItem é importado
import { DashboardStats, EnterpriseService } from '../../../services/enterprise.service'; // <<< ADICIONADO: Importar EnterpriseService

@Component({
  selector: 'app-dashboard-gc',
  standalone: true,
  imports: [
      CommonModule,
      RouterLink,
      FormsModule,
      DatePipe,
      CurrencyPipe,
      DecimalPipe
    ],
  templateUrl: './dashboard-gc.component.html',
  styleUrls: ['./dashboard-gc.component.css']
})
export class DashboardGcComponent implements OnInit {
  activeComponent = 'componente1';

  myGiftCards: GiftCard[] = [];
  isLoading = true;

  validationCode: string = '';
  validationResult: OrderItem | null = null;
  isValidating: boolean = false;
  isPopupVisible = false;

  usedItemsHistory: OrderItem[] = [];
  isLoadingHistory: boolean = false;

  dashboardStats: DashboardStats | null = null;
  isLoadingStats: boolean = true;

  allSalesData: OrderItem[] = [];
  filteredSales: OrderItem[] = [];
  totalAmountReceived: number = 0;
  isLoadingSales: boolean = false;

  selectedProductFilter: string | undefined;
  selectedMonthFilter: number | undefined;
  selectedYearFilter: number | undefined;

  months: { name: string, value: number }[] = [
    { name: 'Janeiro', value: 1 }, { name: 'Fevereiro', value: 2 }, { name: 'Março', value: 3 },
    { name: 'Abril', value: 4 }, { name: 'Maio', value: 5 }, { name: 'Junho', value: 6 },
    { name: 'Julho', value: 7 }, { name: 'Agosto', value: 8 }, { name: 'Setembro', value: 9 },
    { name: 'Outubro', value: 10 }, { name: 'Novembro', value: 11 }, { name: 'Dezembro', value: 12 }
  ];
  availableYears: number[] = [];

  statusTranslations: { [key: string]: string } = {
    'APPROVED': 'Aprovado', 'PENDING': 'Pendente', 'REJECTED': 'Rejeitado',
    'EXPIRED': 'Expirado', 'REFUNDED': 'Estornado', 'VALID': 'Válido',
    'USED': 'Utilizado', 'PARTIALLY_USED': 'Parcialmente Utilizado'
  };

  constructor(
    private giftcardService: GiftcardService,
    private notificationService: NotificationService,
    private confirmationService: ConfirmationService,
    private enterpriseService: EnterpriseService // <<< ADICIONADO: Injetar EnterpriseService
  ) { }

  ngOnInit(): void {
    this.loadMyGiftCards();
    this.generateYearOptions();
    this.loadDashboardStats();
  }

  translateStatus(status: string): string {
    return this.statusTranslations[status] || status;
  }

  showComponent(name: string) {
    this.activeComponent = name;
    if (name === 'componente3' && this.allSalesData.length === 0) {
      this.loadSalesData();
    }
    if (name === 'componente2') {
      if (this.usedItemsHistory.length === 0) {
        this.loadUsedItemsHistory();
      }
    }
  }

  loadDashboardStats(): void {
    this.isLoadingStats = true;
    this.enterpriseService.getDashboardStats().subscribe({
      next: (data) => {
        this.dashboardStats = data;
        this.isLoadingStats = false;
      },
      error: (err) => {
        console.error("Erro ao carregar estatísticas do dashboard:", err);
        this.notificationService.show("Não foi possível carregar as estatísticas.", "error");
        this.dashboardStats = null; // Reseta em caso de erro
        this.isLoadingStats = false;
      }
    });
  }

  loadMyGiftCards(): void {
    this.isLoading = true;
    this.giftcardService.getMyGiftCards().subscribe({
      next: (data) => {
        this.myGiftCards = data;
        this.myGiftCards.sort((a, b) => a.title.localeCompare(b.title));
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
      confirmText: 'Excluir', cancelText: 'Manter'
    }).subscribe(confirmed => {
      if (confirmed) {
        this.giftcardService.deleteGiftCard(id).subscribe({
          next: () => {
            this.notificationService.show('Gift card excluído!', 'success');
            this.myGiftCards = this.myGiftCards.filter(gc => gc.id !== id);
            if (this.activeComponent === 'componente3') {
              this.loadSalesData();
            }
          },
          error: () => this.notificationService.show('Falha ao excluir o gift card.', 'error')
        });
      }
    });
  }

  generateYearOptions(): void {
    const currentYear = new Date().getFullYear();
    for (let i = 0; i < 5; i++) {
      this.availableYears.push(currentYear - i);
    }
    this.availableYears.sort((a, b) => b - a);
  }

  loadSalesData(): void {
    this.isLoadingSales = true;
    // <<< CORREÇÃO: Usar enterpriseService para chamar o método correto >>>
    this.enterpriseService.getEnterpriseSalesHistory(
      this.selectedProductFilter,
      this.selectedMonthFilter,
      this.selectedYearFilter
    ).subscribe({
      next: (data: OrderItem[]) => {
        this.allSalesData = data;
        this.filteredSales = data;
        this.calculateTotalAmountReceived();
        this.isLoadingSales = false;
      },
      error: () => {
        this.notificationService.show('Não foi possível carregar o histórico de vendas.', 'error');
        this.allSalesData = [];
        this.filteredSales = [];
        this.totalAmountReceived = 0;
        this.isLoadingSales = false;
      }
    });
  }

  applySalesFilters(): void {
    this.loadSalesData();
  }

  clearSalesFilters(): void {
    this.selectedProductFilter = undefined;
    this.selectedMonthFilter = undefined;
    this.selectedYearFilter = undefined;
    this.loadSalesData();
  }

  calculateTotalAmountReceived(): void {
    this.totalAmountReceived = this.filteredSales.reduce((sum, item) => {
      const orderInfo = item.order;
      const orderStatus = orderInfo ? (orderInfo as any).status : null;
      if (orderStatus === 'APPROVED') {
          const amount = +(item.seller_amount || 0);
          return sum + amount;
      }
      return sum;
    }, 0);
  }

   loadUsedItemsHistory(): void {
    this.isLoadingHistory = true;
    // <<< CORREÇÃO: Usar giftcardService para o histórico de VALIDAÇÃO >>>
    this.giftcardService.getUsedGiftCardsHistory().subscribe({
      next: (data) => {
        this.usedItemsHistory = data.sort((a, b) =>
           new Date(b.order?.created_at || 0).getTime() - new Date(a.order?.created_at || 0).getTime()
        );
        this.isLoadingHistory = false;
      },
      error: () => {
        this.notificationService.show('Não foi possível carregar o histórico de validações.', 'error');
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
    // <<< CORREÇÃO: Usar giftcardService para validar o código >>>
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
    if (!this.validationResult || !['VALID', 'PARTIALLY_USED'].includes(this.validationResult.status)) {
        this.notificationService.show('Apenas códigos válidos ou parcialmente usados podem ser marcados.', 'warning');
        return;
    };
    const codeToMark = this.validationCode;
    // <<< CORREÇÃO: Usar giftcardService para marcar como usado >>>
    this.giftcardService.markGiftCardCodeAsUsed(codeToMark).subscribe({
      next: (updatedItem) => {
        this.notificationService.show(`Código ${codeToMark} marcado como utilizado!`, 'success');
        this.closePopup();
        this.loadUsedItemsHistory();
        if (this.allSalesData.length > 0) {
            this.loadSalesData();
        }
      },
      error: (err) => this.notificationService.show(err.error.detail || 'Erro ao marcar código como usado.', 'error')
    });
  }

  closePopup(): void {
    this.isPopupVisible = false;
    this.validationResult = null;
    this.validationCode = '';
  }
}