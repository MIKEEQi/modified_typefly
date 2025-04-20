.PHONY: stop, start, remove, open, build, clean

SERVICE_LIST = router yolo
SIF_DIR = ./sif

validate_service:
ifeq ($(filter $(SERVICE),$(SERVICE_LIST)),)
	@echo Invalid SERVICE: [$(SERVICE)], valid values are [$(SERVICE_LIST)]
	$(error Invalid SERVICE, valid values are [$(SERVICE_LIST)])
endif

stop: validate_service
	@echo "=> Stopping typefly-$(SERVICE)..."
	@pkill -f "typefly-$(SERVICE)_0.1.sif" || true

start: validate_service
	@echo "=> Starting typefly-$(SERVICE)..."
	singularity run --nv \
		--bind $(PWD):/workspace \
		--env ROOT_PATH="/workspace" \
		--env ROUTER_SERVICE_PORT="50049" \
		--env YOLO_SERVICE_PORT="50050,50051,50052" \
		$(SIF_DIR)/typefly-$(SERVICE)_0.1.sif &

remove: validate_service
	@echo "=> Removing typefly-$(SERVICE)..."
	@rm -f $(SIF_DIR)/typefly-$(SERVICE).sif

open: validate_service
	@echo "=> Opening shell in typefly-$(SERVICE)..."
	singularity shell --nv --bind $(PWD):/app $(SIF_DIR)/typefly-$(SERVICE).sif

build: validate_service
	@echo "=> Building typefly-$(SERVICE)..."
	@mkdir -p $(SIF_DIR)
	singularity build --fakeroot $(SIF_DIR)/typefly-$(SERVICE)_0.1.sif docker-daemon://typefly-$(SERVICE):0.1

typefly:
	bash ./serving/webui/install_requirements.sh
	cd ./proto && bash generate.sh
	python3 ./serving/webui/typefly.py --use_virtual_robot
