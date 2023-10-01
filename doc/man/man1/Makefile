SRCDIR = ../../txt
SOURCES := $(SRCDIR)/sas_counters.txt \
	   $(SRCDIR)/sas_devices.txt \
	   $(SRCDIR)/sas_discover.txt \
	   $(SRCDIR)/ses_report.txt
OBJECTS  := $(SOURCES:$(SRCDIR)/%.txt=%.1)

%.1: ../../txt/%.txt
	rst2man $< $@

all: $(OBJECTS)

force: clean all

clean:
	@rm -v $(OBJECTS)
