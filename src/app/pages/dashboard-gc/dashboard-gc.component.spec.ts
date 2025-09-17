import { ComponentFixture, TestBed } from '@angular/core/testing';

import { DashboardGcComponent } from './dashboard-gc.component';

describe('DashboardGcComponent', () => {
  let component: DashboardGcComponent;
  let fixture: ComponentFixture<DashboardGcComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [DashboardGcComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(DashboardGcComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
