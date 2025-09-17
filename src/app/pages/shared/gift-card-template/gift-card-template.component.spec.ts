import { ComponentFixture, TestBed } from '@angular/core/testing';

import { GiftCardTemplateComponent } from './gift-card-template.component';

describe('GiftCardTemplateComponent', () => {
  let component: GiftCardTemplateComponent;
  let fixture: ComponentFixture<GiftCardTemplateComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [GiftCardTemplateComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(GiftCardTemplateComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
